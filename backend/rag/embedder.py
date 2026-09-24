"""
RAG Embedder — Gemini text embeddings (cloud, 768d)

This module is the only runtime entry point for embedding generation used by:
1) offline ingestion
2) online retrieval query embedding
"""

import logging
import os
import time
from typing import List, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
# Preferred model can be overridden via GEMINI_EMBED_MODEL.
# Keep fallback candidates because availability can vary by key/version.
MODEL           = os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001")
DIMENSIONS      = 768
BATCH_SIZE      = 20     # log progress every N chunks
MAX_RETRIES     = 3
BASE_BACKOFF    = 2.0    # seconds
MAX_INPUT_CHARS = 3000   # nomic-embed-text safe context limit (≈750 tokens)

_MODEL_CANDIDATES = (
    MODEL,
    "models/gemini-embedding-001",
    "models/gemini-embedding-2-preview",
    "gemini-embedding-001",
)

_active_model: Optional[str] = None


def _configure_gemini() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is required for embeddings.")
    return genai.Client(api_key=api_key)


def _is_model_not_found(error: Exception) -> bool:
    msg = str(error).lower()
    return "404" in msg and ("not found" in msg or "is not supported" in msg)


def _embed_with_fallback(client: genai.Client, content: str, task_type: str) -> List[float]:
    """Try the active model first, then fallback candidates."""
    global _active_model

    candidates: List[str] = []
    if _active_model:
        candidates.append(_active_model)
    for m in _MODEL_CANDIDATES:
        if m not in candidates:
            candidates.append(m)

    last_error = None

    for model_name in candidates:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.models.embed_content(  # type: ignore[reportUnknownMemberType]
                    model=model_name,
                    contents=content,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=DIMENSIONS,
                    ),
                )
                embedding = []
                if getattr(response, "embeddings", None):
                    first = response.embeddings[0] if response.embeddings else None
                    embedding = list(first.values) if first and first.values else []
                if not embedding:
                    raise RuntimeError("Gemini returned empty embedding.")
                if len(embedding) != DIMENSIONS:
                    raise RuntimeError(
                        f"Embedding dimension mismatch: expected {DIMENSIONS}, got {len(embedding)}. "
                        "Set GEMINI_EMBED_MODEL to a model supporting output_dimensionality "
                        "or migrate vector dimensions in rag models/migrations."
                    )
                _active_model = model_name
                return embedding
            except Exception as exc:
                last_error = exc
                if _is_model_not_found(exc):
                    logger.warning(
                        "[Embedder] Model '%s' unavailable for embed_content, trying next candidate.",
                        model_name,
                    )
                    break

                wait = BASE_BACKOFF * attempt
                logger.warning(
                    "[Embedder] model=%s attempt %d/%d failed: %s. Retrying in %.0fs...",
                    model_name,
                    attempt,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                time.sleep(wait)

    raise RuntimeError(
        f"Embedding failed across all model candidates: {last_error}. "
        "Set GEMINI_EMBED_MODEL in backend/.env to a model your key supports."
    )


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string. Used for ONLINE query embedding at request time.

    Args:
        text: Natural language query from the student.

    Returns:
        768-dimensional float list.

    Raises:
        ValueError: if text is empty.
        RuntimeError: if Gemini embedding call fails after retries.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")

    client = _configure_gemini()
    t0 = time.perf_counter()
    embedding = _embed_with_fallback(client, text.strip(), task_type="RETRIEVAL_QUERY")
    latency_ms = (time.perf_counter() - t0) * 1000
    logger.debug(f"[Embedder] embed_text: {latency_ms:.1f}ms")
    return embedding


def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts. Used for OFFLINE ingestion only.

    Processes one at a time.
    Batches are logged for progress visibility.

    Args:
        texts: List of natural language chunk texts.

    Returns:
        List of 768-dimensional float lists in the same order as input.

    Raises:
        RuntimeError: if any embedding fails after retries.
    """
    if not texts:
        return []

    client = _configure_gemini()
    all_embeddings: List[List[float]] = []
    total = len(texts)

    for i, text in enumerate(texts, 1):
        text = text.strip()
        if not text:
            logger.warning(f"[Embedder] Skipping empty text at position {i}")
            all_embeddings.append([0.0] * DIMENSIONS)
            continue

        # Truncate to safe context limit
        if len(text) > MAX_INPUT_CHARS:
            logger.warning(
                f"[Embedder] Chunk {i}/{total} truncated from {len(text)} "
                f"to {MAX_INPUT_CHARS} chars (context limit)"
            )
            text = text[:MAX_INPUT_CHARS].rsplit(" ", 1)[0]

        t0 = time.perf_counter()
        emb = _embed_with_fallback(client, text, task_type="RETRIEVAL_DOCUMENT")
        latency_ms = (time.perf_counter() - t0) * 1000
        all_embeddings.append(emb)

        if i % BATCH_SIZE == 0 or i == total:
            logger.info(
                f"[Embedder] Progress: {i}/{total} chunks embedded "
                f"(last {latency_ms:.0f}ms)"
            )

    return all_embeddings
