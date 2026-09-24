"""
RAG Chunker — Rule-Based Educational Content Chunker

Splits raw document text into semantically meaningful KnowledgeChunk candidates.
Uses regex heuristics to detect chunk types — no LLM involved (v1).

Philosophy:
  - Chunk by LEARNING INTENT, not by token count
  - Soft bounds: 300-650 tokens (never split a semantic unit to hit a target)
  - 7 universal chunk types apply across Math / Science / CS
  - Hard validators discard noise before embedding
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Soft token bounds ────────────────────────────────────────────────────────
MIN_TOKENS    = 40        # Hard-fail minimum
SOFT_MIN      = 80        # Ideal minimum — lower to avoid giant merged chunks
SOFT_MAX      = 650       # Ideal maximum (warn if above)
HARD_MAX_CHARS = 800      # Force-split any block larger than this (≈200 tokens)

# ── Regex patterns for chunk type detection ──────────────────────────────────
_PATTERNS = {
    "definition": re.compile(
        r"is defined as|is called|means that|refers to|we define|by definition|"
        r"^(definition|def\.?)[\s:—]",
        re.IGNORECASE | re.MULTILINE,
    ),
    "rule": re.compile(
        r"theorem|law of|formula|O\(|Ω\(|Θ\(|\\[a-zA-Z]|"
        r"is given by|states that|rule:|[≤≥≈≡∈∉∩∪∑∏∂∇]|"
        r"complexity is|time complexity|space complexity",
        re.IGNORECASE,
    ),
    "procedure": re.compile(
        r"^\s*\d+[\.\)]\s+|step \d|^(step|phase|stage)[\s:—]|"
        r"\b(algorithm|first[,:]|then[,:]|finally[,:]|"
        r"apply|compute|calculate|initialize|iterate|repeat)\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "example": re.compile(
        r"^(example|ex\.|e\.g\.|for example|consider|given|"
        r"let's say|suppose|sample|illustration)[\s:—]|"
        r"input:.*output:|problem:.*solution:",
        re.IGNORECASE | re.MULTILINE,
    ),
    "comparison": re.compile(
        r"\bvs\.?\b|\bversus\b|difference between|compared to|"
        r"unlike|in contrast|on the other hand|whereas|"
        r"better than|worse than|trade.?off",
        re.IGNORECASE,
    ),
    "concept": re.compile(
        r"intuitively|think of (it|this)|the (key )?idea|essentially|"
        r"in simple terms|at a high level|the intuition|"
        r"why (does|do|is|are)|how (does|do)",
        re.IGNORECASE,
    ),
    # "mistake" is never auto-detected — manually seeded only
}

# Priority order: more specific patterns win over more general ones
_TYPE_PRIORITY = ["example", "rule", "procedure", "definition", "comparison", "concept"]

# ── Junk patterns (hard-fail validator) ──────────────────────────────────────
_JUNK_PATTERNS = [
    re.compile(r"\.{4,}"),                       # table of contents: "Chapter 1 ...... 4"
    re.compile(r"^\[\d+\]", re.MULTILINE),        # reference list: "[1] Author et al."
    re.compile(r"figure \d+[:.]", re.IGNORECASE), # figure captions
    re.compile(r"table \d+[:.]", re.IGNORECASE),  # table captions
    re.compile(r"^page \d+$", re.IGNORECASE | re.MULTILINE),
]

# ── Dangling reference patterns ───────────────────────────────────────────────
_DANGLING_PATTERNS = re.compile(
    r"^(as (we saw|shown|mentioned|discussed|stated) (above|below|earlier|previously)|"
    r"(this|these|the above|the following) (shows?|demonstrates?|illustrates?|"
    r"refers? to|means?|is|are)|see (figure|table|section|chapter) \d+)",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class ChunkCandidate:
    """
    A candidate chunk produced by the chunker, before DB insertion.

    `text` is the embedding target — must be natural language.
    `formula_latex` and `formula_plain` are metadata only.
    `parent_hint` tells the ingestion pipeline which chunk_type this depends on.
    """
    text: str
    chunk_type: str                  # one of the 7 types
    chunk_index: int                 # sequential index within the document
    source_file: str = ""
    source_page: int = 0
    concept_tag: str = ""
    difficulty: str = "medium"
    formula_latex: str = ""
    formula_plain: str = ""
    parent_hint: str = ""            # "procedure" means this chunk should link to its nearest procedure parent


class EducationalChunker:
    """
    Rule-based chunker for educational content.

    Usage:
        chunker = EducationalChunker()
        candidates = chunker.chunk_document(text, source_file="lecture.pdf", concept_tag="Binary Search")
        valid = [c for c in candidates if chunker.validate(c)]
    """

    def chunk_document(
        self,
        text: str,
        source_file: str = "",
        concept_tag: str = "",
        difficulty: str = "medium",
    ) -> List[ChunkCandidate]:
        """
        Main entry point. Returns a list of ChunkCandidates (unvalidated).

        Args:
            text:         Full cleaned document text.
            source_file:  Name of the source file for provenance.
            concept_tag:  Concept label (e.g. "Binary Search").
            difficulty:   Default difficulty for all chunks.
        """
        raw_blocks = self._split_on_boundaries(text)
        candidates = []

        for idx, block in enumerate(raw_blocks):
            block = block.strip()
            if not block:
                continue

            chunk_type = self._detect_chunk_type(block)
            formula_latex, formula_plain = self._extract_formula(block)

            # Determine parent_hint for examples and mistakes
            parent_hint = ""
            if chunk_type in ("example", "mistake"):
                parent_hint = "procedure"

            candidates.append(ChunkCandidate(
                text=self._strip_formula_from_text(block),
                chunk_type=chunk_type,
                chunk_index=idx,
                source_file=source_file,
                concept_tag=concept_tag,
                difficulty=difficulty,
                formula_latex=formula_latex,
                formula_plain=formula_plain,
                parent_hint=parent_hint,
            ))

        logger.info(f"[Chunker] {source_file}: produced {len(candidates)} raw candidates")
        return candidates

    # ── Boundary splitting ────────────────────────────────────────────────────

    def _split_on_boundaries(self, text: str) -> List[str]:
        """
        Split document text into semantic blocks.

        Handles both:
          - Structured documents (Markdown headings, horizontal rules)
          - Plain-text PDFs (paragraph breaks = double newlines)

        After splitting, merges tiny blocks up to SOFT_MIN tokens,
        then hard-splits any block exceeding HARD_MAX_CHARS at sentence boundaries.
        """
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Primary boundary pattern — order matters: most specific first
        boundary = re.compile(
            r"^(#{1,4}\s+.+)$"    # Markdown headings: ## Heading
            r"|^[-=_]{3,}\s*$"    # Horizontal rules: ---  ===  ___
            r"|\n{2,}",           # Double (or more) blank lines — plain PDF paragraphs
            re.MULTILINE,
        )

        parts = [p.strip() for p in boundary.split(text) if p and p.strip()]

        # ── Merge tiny blocks up to SOFT_MIN ────────────────────────────────
        merged: List[str] = []
        buffer = ""

        for part in parts:
            buffer = (buffer + "\n\n" + part).strip() if buffer else part
            if self._approx_token_count(buffer) >= SOFT_MIN:
                merged.append(buffer)
                buffer = ""

        if buffer:
            merged.append(buffer)

        # ── Hard-split any block exceeding HARD_MAX_CHARS ───────────────────
        final: List[str] = []
        for block in merged:
            if len(block) <= HARD_MAX_CHARS:
                final.append(block)
            else:
                # Split at sentence boundaries within the block
                final.extend(self._hard_split(block))

        return final

    def _hard_split(self, text: str) -> List[str]:
        """
        Force-split a too-large block at sentence boundaries.
        Splits on '. ', '? ', '! ' followed by a capital letter.
        Produces chunks of up to HARD_MAX_CHARS each.
        """
        # Split on sentence-ending punctuation
        sentence_end = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = sentence_end.split(text)

        chunks: List[str] = []
        buffer = ""

        for sentence in sentences:
            candidate = (buffer + " " + sentence).strip() if buffer else sentence
            if len(candidate) > HARD_MAX_CHARS and buffer:
                # Flush current buffer and start fresh
                chunks.append(buffer)
                buffer = sentence
            else:
                buffer = candidate

        if buffer:
            chunks.append(buffer)

        return chunks if chunks else [text[:HARD_MAX_CHARS]]

    # ── Chunk type detection ──────────────────────────────────────────────────

    def _detect_chunk_type(self, text: str) -> str:
        """
        Detect chunk type from text using regex heuristics.
        Returns one of the 7 type strings. Defaults to 'concept'.
        """
        for chunk_type in _TYPE_PRIORITY:
            if _PATTERNS[chunk_type].search(text):
                return chunk_type
        return "concept"

    # ── Formula extraction ────────────────────────────────────────────────────

    def _extract_formula(self, text: str) -> tuple[str, str]:
        """
        Extract LaTeX formulas from text.
        Returns (formula_latex, formula_plain).
        plain is the latex with backslashes stripped — good enough for TTS context.
        """
        # Match inline LaTeX: $...$ or $$...$$
        latex_pattern = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$", re.DOTALL)
        matches = latex_pattern.findall(text)

        if not matches:
            return "", ""

        # Take the first formula found
        formula_latex = next((m[0] or m[1] for m in matches if m[0] or m[1]), "")
        formula_latex = formula_latex.strip()

        # Convert to plain text for TTS: strip latex commands
        formula_plain = re.sub(r"\\[a-zA-Z]+", " ", formula_latex)     # \frac → space
        formula_plain = re.sub(r"[{}_^\\]", " ", formula_plain)        # braces, subscripts
        formula_plain = re.sub(r"\s+", " ", formula_plain).strip()

        return formula_latex, formula_plain

    def _strip_formula_from_text(self, text: str) -> str:
        """
        Remove LaTeX formula syntax from text so the embedding target is clean natural language.
        Keep the surrounding explanation — just remove the $...$ markers.
        """
        # Replace $$...$$ with a placeholder
        text = re.sub(r"\$\$(.+?)\$\$", r" (formula) ", text, flags=re.DOTALL)
        text = re.sub(r"\$(.+?)\$", r" (formula) ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ── Validators (hard-fail gates) ──────────────────────────────────────────

    def validate(self, chunk: ChunkCandidate) -> bool:
        """
        Run all hard-fail validators on a chunk.
        Returns True if the chunk passes all checks, False if it should be discarded.
        """
        text = chunk.text

        # 1. Minimum length
        if self._approx_token_count(text) < MIN_TOKENS:
            logger.debug(f"[Validator] FAIL min_length: '{text[:60]}'")
            return False

        # 2. Junk patterns (TOC, refs, figure captions, page numbers)
        for pattern in _JUNK_PATTERNS:
            if pattern.search(text):
                logger.debug(f"[Validator] FAIL junk_pattern: '{text[:60]}'")
                return False

        # 3. Dangling references at the start of the chunk
        if _DANGLING_PATTERNS.search(text[:200]):
            logger.debug(f"[Validator] FAIL dangling_ref: '{text[:60]}'")
            return False

        # 4. Formula integrity: if latex is set, plain must also be set
        if chunk.formula_latex and not chunk.formula_plain:
            logger.warning(
                f"[Validator] FAIL formula_integrity: latex set but plain is empty. "
                f"Chunk: '{text[:60]}'"
            )
            return False

        return True

    # ── Deduplication ─────────────────────────────────────────────────────────

    def deduplicate(
        self,
        candidates: List[ChunkCandidate],
        existing_embeddings: Optional[List[List[float]]] = None,
        threshold: float = 0.97,
    ) -> List[ChunkCandidate]:
        """
        Remove near-duplicate chunks from the candidate list.

        Deduplication strategy:
          1. Within the new batch: compute pairwise cosine similarity.
             Cosine > threshold → keep the first occurrence.
          2. Against existing DB embeddings (if provided): same threshold.

        Note: This requires embeddings to already be computed.
              Call deduplicate_with_embeddings() after batch embedding.
        """
        seen_texts: set[str] = set()
        unique: List[ChunkCandidate] = []

        for c in candidates:
            # Exact text dedup (cheap)
            normalized = " ".join(c.text.lower().split())
            if normalized in seen_texts:
                logger.debug(f"[Dedup] Exact duplicate dropped: '{c.text[:60]}'")
                continue
            seen_texts.add(normalized)
            unique.append(c)

        logger.info(f"[Dedup] {len(candidates)} → {len(unique)} after exact dedup")
        return unique

    def deduplicate_with_embeddings(
        self,
        candidates: List[ChunkCandidate],
        embeddings: List[List[float]],
        existing_embeddings: Optional[List[List[float]]] = None,
        threshold: float = 0.97,
    ) -> tuple[List[ChunkCandidate], List[List[float]]]:
        """
        Deduplicate candidates using cosine similarity on embeddings.
        Returns filtered (candidates, embeddings) pair.
        """
        import numpy as np

        def cosine(a, b):
            a, b = np.array(a), np.array(b)
            denom = (np.linalg.norm(a) * np.linalg.norm(b))
            return float(np.dot(a, b) / denom) if denom > 0 else 0.0

        kept_candidates = []
        kept_embeddings = []

        for i, (candidate, emb) in enumerate(zip(candidates, embeddings)):
            is_dup = False

            # Check against already-kept candidates
            for kept_emb in kept_embeddings:
                if cosine(emb, kept_emb) > threshold:
                    is_dup = True
                    break

            # Check against existing DB embeddings
            if not is_dup and existing_embeddings:
                for existing_emb in existing_embeddings:
                    if cosine(emb, existing_emb) > threshold:
                        is_dup = True
                        break

            if is_dup:
                logger.debug(f"[Dedup] Cosine duplicate dropped: '{candidate.text[:60]}'")
            else:
                kept_candidates.append(candidate)
                kept_embeddings.append(emb)

        logger.info(f"[Dedup] {len(candidates)} → {len(kept_candidates)} after cosine dedup (threshold={threshold})")
        return kept_candidates, kept_embeddings

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _approx_token_count(text: str) -> int:
        """
        Approximate token count by word count (1 word ≈ 1.3 tokens on average).
        Fast and good enough for chunking decisions.
        """
        return int(len(text.split()) * 1.3)


# ── Topic-Guided Chunker ──────────────────────────────────────────────────────

class TopicGuidedChunker(EducationalChunker):
    """
    Chunk a document using an explicit topic hierarchy provided by the user.

    Each main topic  → one "concept" chunk (concept_tag = topic name)
    Each sub-topic   → one chunk linked to the parent topic chunk
                       (concept_tag = topic name, parent_hint = "concept")

    Section boundaries are found by searching for heading-like occurrences
    of topic/subtopic names in the raw PDF text.
    """

    def chunk_with_topics(
        self,
        text: str,
        topics: List[dict],
        source_file: str = "",
        difficulty: str = "medium",
    ) -> List[ChunkCandidate]:
        """
        Main entry point for topic-guided chunking.

        Args:
            text:       Full cleaned document text (from PyMuPDF).
            topics:     List of {"name": str, "subtopics": [str, ...]}
            source_file: Name of the source file for provenance.
            difficulty:  Default difficulty for all chunks.

        Returns:
            List of ChunkCandidates ordered main-topic first, sub-topics after.
        """
        topic_names = [t["name"] for t in topics]
        topic_sections = self._find_sections(text, topic_names)

        candidates: List[ChunkCandidate] = []
        chunk_idx = 0

        for topic in topics:
            topic_name = topic["name"]
            topic_text = topic_sections.get(topic_name, "").strip()
            subtopics   = topic.get("subtopics", [])

            if not topic_text:
                logger.debug(f"[TopicChunker] No text found for topic: '{topic_name}'")
                continue

            if not subtopics:
                # ── No subtopics: single chunk for the whole topic ────────────
                for part in self._sized_parts(topic_text):
                    if self._approx_token_count(part) < MIN_TOKENS:
                        continue
                    candidates.append(ChunkCandidate(
                        text=part,
                        chunk_type=self._detect_chunk_type(part),
                        chunk_index=chunk_idx,
                        source_file=source_file,
                        concept_tag=topic_name,
                        difficulty=difficulty,
                        parent_hint="",
                    ))
                    chunk_idx += 1
            else:
                # ── With subtopics ────────────────────────────────────────────

                # Overview text (text before the first subtopic heading)
                overview = self._get_overview_text(topic_text, subtopics)
                if overview and self._approx_token_count(overview) >= MIN_TOKENS:
                    candidates.append(ChunkCandidate(
                        text=overview,
                        chunk_type="concept",
                        chunk_index=chunk_idx,
                        source_file=source_file,
                        concept_tag=topic_name,
                        difficulty=difficulty,
                        parent_hint="",   # main chunk — no parent
                    ))
                    chunk_idx += 1

                # Sub-topic sections
                subtopic_sections = self._find_sections(topic_text, subtopics)
                for subtopic_name in subtopics:
                    sub_text = subtopic_sections.get(subtopic_name, "").strip()
                    if not sub_text:
                        continue
                    for part in self._sized_parts(sub_text):
                        if self._approx_token_count(part) < MIN_TOKENS:
                            continue
                        candidates.append(ChunkCandidate(
                            text=part,
                            chunk_type=self._detect_chunk_type(part),
                            chunk_index=chunk_idx,
                            source_file=source_file,
                            concept_tag=topic_name,          # same tag as parent
                            difficulty=difficulty,
                            parent_hint="concept",            # links to parent concept chunk
                        ))
                        chunk_idx += 1

        logger.info(
            f"[TopicChunker] '{source_file}': {len(candidates)} candidates "
            f"from {len(topics)} topics"
        )
        return candidates

    # ── Section finding ───────────────────────────────────────────────────────

    def _find_sections(self, text: str, names: List[str]) -> dict:
        """
        Find text sections for each name by locating heading-like occurrences.

        A heading match is: name appearing on its own line (with optional
        numeric prefix like "1." or "2)") followed by a newline.

        Falls back to first keyword occurrence if heading not found.
        """
        text_lower = text.lower()
        positions: List[tuple] = []  # (char_pos, name)

        for name in names:
            name_lower = name.lower()
            pos = self._find_heading_pos(text_lower, name_lower)
            if pos is not None:
                positions.append((pos, name))

        positions.sort(key=lambda x: x[0])

        sections = {}
        for i, (pos, name) in enumerate(positions):
            end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            sections[name] = text[pos:end].strip()

        # Empty for not-found names
        for name in names:
            if name not in sections:
                sections[name] = ""

        return sections

    def _find_heading_pos(self, text_lower: str, name_lower: str) -> Optional[int]:
        """
        Return the character position immediately AFTER a heading line
        containing `name_lower`.

        Tries three patterns in order:
          1. "1. Name\n"  or "Name\n"  (standalone line with optional number)
          2. Name anywhere as a complete word/phrase on a line
          3. First keyword occurrence (fallback)
        """
        patterns = [
            # Pattern 1: optional number + name on its own line
            rf'(?:^|\n)\s*(?:\d+[\.\)]\s*)?{re.escape(name_lower)}\s*\n',
            # Pattern 2: name at end of a line
            rf'(?:^|\n)\s*(?:\d+[\.\)]\s*)?{re.escape(name_lower)}\s*$',
            # Pattern 3: name anywhere as word boundary (fallback)
            rf'\b{re.escape(name_lower)}\b',
        ]
        for pattern in patterns:
            m = re.search(pattern, text_lower, re.MULTILINE)
            if m:
                # Return position after the end of the match (start of content)
                return m.end()
        return None

    def _get_overview_text(self, topic_text: str, subtopics: List[str]) -> str:
        """Return text before the first subtopic heading within a topic section."""
        text_lower = topic_text.lower()
        first_pos = len(topic_text)
        for subtopic in subtopics:
            pos = self._find_heading_pos(text_lower, subtopic.lower())
            if pos is not None:
                # Adjust: _find_heading_pos returns end of match; go back to start
                m_start = max(0, pos - len(subtopic) - 5)
                first_pos = min(first_pos, m_start)
        return topic_text[:first_pos].strip()

    def _sized_parts(self, text: str) -> List[str]:
        """Split text into parts no larger than HARD_MAX_CHARS."""
        if len(text) <= HARD_MAX_CHARS:
            return [text]
        return self._hard_split(text)
