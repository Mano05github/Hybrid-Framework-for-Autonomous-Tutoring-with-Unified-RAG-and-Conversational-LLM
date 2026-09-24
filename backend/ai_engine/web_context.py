"""
Web Context Fetcher
===================
Fetches accurate, trusted educational content from the web when the local
RAG knowledge base has no relevant material for the student's question.

Tier 1: Wikipedia REST API  (no API key, encyclopedic, always reliable)
Tier 2: DuckDuckGo Instant  (no API key, broad coverage)

Hard timeout: 4 seconds total so it never slows down the teaching response.
"""

import re
import logging
import urllib.request
import urllib.parse
import urllib.error
import json
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── Trusted educational domains for context feedback ──────────────────────
TRUSTED_SOURCES = ["Wikipedia", "DuckDuckGo / Britannica"]

# ── Stop-words stripped when extracting the core topic ────────────────────
_QUERY_STOP = {
    "teach", "me", "about", "the", "explain", "what", "is", "are",
    "how", "does", "work", "tell", "show", "describe", "define",
    "a", "an", "of", "in", "for", "to", "and", "or",
    "structure", "give", "please", "i", "want", "know", "learn",
}


@dataclass
class WebContext:
    text: str               # Clean factual summary (max ~600 chars)
    source_name: str        # e.g. "Wikipedia"
    source_url: str         # canonical URL for citation


# ─────────────────────────────────────────────────────────────────────────────
# Topic extraction
# ─────────────────────────────────────────────────────────────────────────────

def _extract_topic(query: str) -> str:
    """
    Strip instructional verbs and stop-words to get the core concept.

    "teach me about the structure of mitochondria" → "mitochondria"
    "explain the quadratic formula"                → "quadratic formula"
    "what is photosynthesis"                       → "photosynthesis"
    """
    q = query.lower().strip()

    # Remove leading instructional phrases
    q = re.sub(
        r"^(teach me about|explain|describe|tell me about|what is|what are"
        r"|how does|how do|give me|show me|i want to (know|learn) about"
        r"|help me understand)\s+",
        "", q
    )

    # Remove "the structure of", "the concept of" etc.
    q = re.sub(r"^(the\s+)?(structure|concept|definition|meaning)\s+of\s+", "", q)

    # Remove remaining stop-words at the start
    words = q.split()
    while words and words[0] in _QUERY_STOP:
        words.pop(0)

    topic = " ".join(words).strip()
    return topic if topic else query.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Tier 1 — Wikipedia REST API
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_wikipedia(topic: str, timeout: float = 3.0) -> Optional[WebContext]:
    """
    Wikipedia /page/summary/{title} endpoint.
    Returns a structured summary paragraph.
    """
    title = urllib.parse.quote(topic.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Vaathiyar-EducationBot/1.0 (educational platform)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))

        extract = data.get("extract", "").strip()
        if not extract or data.get("type") == "disambiguation":
            return None

        # Trim to ~600 chars at a sentence boundary
        if len(extract) > 600:
            trimmed = extract[:600]
            last_dot = trimmed.rfind(". ")
            extract = trimmed[: last_dot + 1] if last_dot > 100 else trimmed

        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", url)
        logger.info(f"[WebContext] Wikipedia hit for '{topic}'")
        return WebContext(text=extract, source_name="Wikipedia", source_url=page_url)

    except Exception as e:
        logger.debug(f"[WebContext] Wikipedia failed for '{topic}': {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Tier 2 — DuckDuckGo Instant Answer API
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_duckduckgo(topic: str, timeout: float = 3.0) -> Optional[WebContext]:
    """
    DuckDuckGo Instant Answer API — returns AbstractText from Wikipedia /
    Britannica / CliffsNotes etc.
    """
    params = urllib.parse.urlencode({
        "q": topic,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
        "skip_disambig": "1",
    })
    url = f"https://api.duckduckgo.com/?{params}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Vaathiyar-EducationBot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        abstract = data.get("AbstractText", "").strip()
        if not abstract:
            return None

        if len(abstract) > 600:
            trimmed = abstract[:600]
            last_dot = trimmed.rfind(". ")
            abstract = trimmed[: last_dot + 1] if last_dot > 100 else trimmed

        source_url = data.get("AbstractURL", "https://duckduckgo.com")
        source_name = data.get("AbstractSource", "DuckDuckGo")
        logger.info(f"[WebContext] DuckDuckGo hit for '{topic}' via {source_name}")
        return WebContext(text=abstract, source_name=source_name, source_url=source_url)

    except Exception as e:
        logger.debug(f"[WebContext] DuckDuckGo failed for '{topic}': {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_web_context(query: str, timeout: float = 4.0) -> Optional[WebContext]:
    """
    Main entry point.  Tries Wikipedia first, then DuckDuckGo.
    Returns the first successful result, or None if both fail.

    Total time budget: `timeout` seconds (default 4s).
    Each tier gets half the remaining budget.
    """
    import time
    start = time.perf_counter()

    topic = _extract_topic(query)
    print(f"  🌐 [WebContext] Fetching context for topic: '{topic}'")

    # Tier 1 — Wikipedia
    tier_timeout = min(timeout * 0.65, 2.5)
    result = _fetch_wikipedia(topic, timeout=tier_timeout)
    if result:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  ✅ [WebContext] Wikipedia ✓ ({elapsed:.0f}ms) — {len(result.text)} chars")
        return result

    # Tier 2 — DuckDuckGo (if time budget allows)
    remaining = timeout - (time.perf_counter() - start)
    if remaining > 0.5:
        result = _fetch_duckduckgo(topic, timeout=remaining)
        if result:
            elapsed = (time.perf_counter() - start) * 1000
            print(f"  ✅ [WebContext] DuckDuckGo/{result.source_name} ✓ ({elapsed:.0f}ms)")
            return result

    elapsed = (time.perf_counter() - start) * 1000
    print(f"  ⚠️  [WebContext] No online context found for '{topic}' ({elapsed:.0f}ms) — using LLM knowledge")
    return None
