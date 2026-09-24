"""
RAG Retriever — Online Runtime Retrieval

Latency target: < 200ms end-to-end (embed + search + assemble)

This module is called from teacher_agent and socratic_agent.
It is the ONLY place at runtime that touches the KnowledgeChunk table.

Pipeline:
    Query → Embed → pgvector cosine search → Intent boost →
    Difficulty bias → Parent co-retrieval → Context assembly → str
"""

import logging
from typing import List, Optional

from .embedder import embed_text
from .models import KnowledgeChunk

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_K = 8
DEFAULT_MAX_CHARS = 2000
CURRENT_INDEX_VERSION = "v2.0"   # gemini text-embedding-004 (768d)
DIMENSIONS = 768

# Canonical ordering of chunk types in assembled context
_CONTEXT_ORDER = [
    "definition",
    "concept",
    "rule",
    "procedure",
    "example",
    "mistake",
    "comparison",
]


def retrieve_context(
    query: str,
    topic_id: int,
    intent: Optional[str] = None,
    difficulty_bias: Optional[str] = None,
    k: int = DEFAULT_K,
    max_chars: int = DEFAULT_MAX_CHARS,
    index_version: str = CURRENT_INDEX_VERSION,
) -> str:
    """
    Main online retrieval entry point. Called from teacher_agent / socratic_agent.

    Args:
        query:           Student's natural language question.
        topic_id:        Django Topic.id to restrict retrieval scope.
        intent:          Learning intent hint from SetFit classifier.
                         One of: definition | concept | rule | procedure | example | mistake | comparison
                         If None, plain cosine search with no boost.
        difficulty_bias: Signal from empath_agent.
                         "struggling" → prioritize examples + mistakes
                         "confident"  → prioritize comparisons + rules
                         None         → no bias
        k:               Number of chunks to retrieve before boost/bias.
        max_chars:       Maximum characters in the assembled context block.
        index_version:   Which index version to query.

    Returns:
        Formatted context string for injection into the LLM prompt.
        Returns "" if retrieval fails or no chunks found.
    """
    if not query or not query.strip():
        return ""

    try:
        # Step 1: Embed the query
        query_vec = embed_text(query)

        # Step 2: pgvector cosine search (filtered)
        chunks = _pgvector_search(query_vec, topic_id, k, index_version)

        if not chunks:
            logger.info(f"[Retriever] No chunks found for topic_id={topic_id}, query='{query[:50]}'")
            return ""

        # Step 3: Intent boost (float matching chunk_type to top)
        chunks = _apply_intent_boost(chunks, intent)

        # Step 4: Difficulty bias (reorder by student state)
        chunks = _apply_difficulty_bias(chunks, difficulty_bias)

        # Step 5: Parent co-retrieval (prepend procedure before its example)
        chunks = _co_retrieve_parents(chunks)

        # Step 6: Assemble labeled context block
        context = _assemble_context_block(chunks, max_chars)

        logger.info(
            f"[Retriever] Retrieved {len(chunks)} chunks for topic={topic_id}, "
            f"intent={intent}, bias={difficulty_bias}, "
            f"context={len(context)} chars"
        )
        return context

    except Exception as e:
        logger.error(f"[Retriever] retrieve_context failed: {e}", exc_info=True)
        return ""


# ── Step 2: pgvector Search ───────────────────────────────────────────────────

def _pgvector_search(
    query_vec: List[float],
    topic_id: int,
    k: int,
    index_version: str,
) -> List[KnowledgeChunk]:
    """
    Perform cosine similarity search in pgvector.

    Uses the HNSW index with filters:
      - topic_id:       only chunks for this topic
      - is_active:      only non-deprecated chunks
      - index_version:  only chunks from the current index
    """
    try:
        from pgvector.django import CosineDistance

        chunks = list(
            KnowledgeChunk.objects.filter(
                topic_id=topic_id,
                is_active=True,
                index_version=index_version,
            )
            .order_by(CosineDistance("embedding", query_vec))
            .select_related("parent_chunk")[:k]
        )
        return chunks

    except Exception as e:
        logger.error(f"[Retriever] pgvector search failed: {e}", exc_info=True)
        return []


# ── Step 3: Intent Boost ──────────────────────────────────────────────────────

def _apply_intent_boost(
    chunks: List[KnowledgeChunk],
    intent: Optional[str],
) -> List[KnowledgeChunk]:
    """
    Float chunks matching the detected intent to the top.
    Does NOT exclude other chunk types — just reorders.
    """
    if not intent:
        return chunks

    matched = [c for c in chunks if c.chunk_type == intent]
    others  = [c for c in chunks if c.chunk_type != intent]
    return matched + others


# ── Step 4: Difficulty Bias ───────────────────────────────────────────────────

def _apply_difficulty_bias(
    chunks: List[KnowledgeChunk],
    difficulty_bias: Optional[str],
) -> List[KnowledgeChunk]:
    """
    Reorder chunks based on student emotional state (from empath_agent).

    struggling → prioritize examples and mistakes (concrete, supportive)
    confident  → prioritize comparisons and rules (advanced, challenging)
    None       → no change
    """
    if not difficulty_bias or not chunks:
        return chunks

    if difficulty_bias == "struggling":
        priority_types = {"example", "mistake", "procedure"}
    elif difficulty_bias == "confident":
        priority_types = {"comparison", "rule", "concept"}
    else:
        return chunks

    priority = [c for c in chunks if c.chunk_type in priority_types]
    rest     = [c for c in chunks if c.chunk_type not in priority_types]
    return (priority + rest)[:len(chunks)]  # preserve total count


# ── Step 5: Parent Co-Retrieval ───────────────────────────────────────────────

def _co_retrieve_parents(chunks: List[KnowledgeChunk]) -> List[KnowledgeChunk]:
    """
    Fetch parent chunks for any example/mistake chunks that have a parent.
    Prepend the parent immediately before its child in the list.

    This ensures examples always appear with their procedure context.
    """
    parent_ids = [
        c.parent_chunk_id
        for c in chunks
        if c.parent_chunk_id is not None
    ]

    if not parent_ids:
        return chunks

    # Batch fetch all parents in one query
    parents_map = {
        p.id: p
        for p in KnowledgeChunk.objects.filter(id__in=parent_ids)
    }

    result: List[KnowledgeChunk] = []
    seen_ids: set = set()

    for chunk in chunks:
        # Insert parent before child if not already in result
        if chunk.parent_chunk_id and chunk.parent_chunk_id in parents_map:
            parent = parents_map[chunk.parent_chunk_id]
            if parent.id not in seen_ids:
                result.append(parent)
                seen_ids.add(parent.id)

        if chunk.id not in seen_ids:
            result.append(chunk)
            seen_ids.add(chunk.id)

    return result


# ── Step 6: Context Assembly ──────────────────────────────────────────────────

def _assemble_context_block(
    chunks: List[KnowledgeChunk],
    max_chars: int,
) -> str:
    """
    Assemble a labeled, ordered context string for LLM injection.

    Ordering follows the canonical learning sequence:
      definition → concept → rule → procedure → example → mistake → comparison

    Output format:
      [1] Definition — Binary Search
      Binary search is a divide-and-conquer algorithm...

      [2] Procedure — Binary Search
      To perform binary search: initialize low=0...
    """
    # Sort by canonical order
    def sort_key(chunk: KnowledgeChunk) -> int:
        try:
            return _CONTEXT_ORDER.index(chunk.chunk_type)
        except ValueError:
            return len(_CONTEXT_ORDER)

    ordered = sorted(chunks, key=sort_key)

    lines: List[str] = []
    total_chars = 0
    label_num = 1

    for chunk in ordered:
        type_label = chunk.chunk_type.replace("_", " ").title()
        header = f"[{label_num}] {type_label} — {chunk.concept_tag}"
        body   = chunk.text.strip()
        entry  = f"{header}\n{body}"

        remaining = max_chars - total_chars - 2  # -2 for \n\n separator

        if remaining <= len(header) + 20:
            # Budget exhausted — stop
            break

        if len(entry) > remaining:
            # Truncate body to fit, never discard entirely
            allowed_body = remaining - len(header) - 1  # -1 for \n
            body = body[:allowed_body].rsplit(" ", 1)[0] + " …"
            entry = f"{header}\n{body}"

        lines.append(entry)
        total_chars += len(entry) + 2
        label_num += 1

    return "\n\n".join(lines)
