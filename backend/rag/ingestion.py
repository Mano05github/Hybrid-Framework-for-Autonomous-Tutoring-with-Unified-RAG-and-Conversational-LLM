"""
RAG Ingestion Pipeline — Offline Knowledge Ingestion

Converts raw educational documents into embedded KnowledgeChunk DB records.
This is a HEAVY, ONE-TIME operation. NEVER call this at request time.

Usage:
    python manage.py ingest_knowledge --source rag/docs/ --topic-id 7 --subject CS

Pipeline:
    Raw Files
      → 3-path page classification (text-only / structured-visual / handwritten)
      → PyMuPDF text extract + find_tables() for structured pages
      → llava-phi3 vision (Ollama) for visual/handwritten pages
      → Clean → Chunk (7 types) → Validate → Deduplicate
      → nomic-embed-text (Ollama) → 768d vectors
      → pgvector bulk insert → parent link
"""

import logging
import json
import re
import time
from pathlib import Path
from typing import List, Optional

from django.db import transaction

from .chunker import ChunkCandidate, EducationalChunker
from .embedder import embed_batch
from .models import KnowledgeChunk

logger = logging.getLogger(__name__)


# ── Document Loaders ──────────────────────────────────────────────────────────

def _extract_tables_as_text(page) -> str:
    """
    Extract tables from a PyMuPDF page as markdown text.
    Uses PyMuPDF's built-in table finder (v1.23+).
    Falls back gracefully if find_tables() is unavailable.
    """
    table_texts = []
    try:
        tables = page.find_tables()
        for table in tables:
            try:
                # Convert to list of rows
                rows = table.extract()
                if not rows:
                    continue
                # Build markdown table
                lines = []
                header = [str(c or "").strip() for c in rows[0]]
                lines.append("| " + " | ".join(header) + " |")
                lines.append("| " + " | ".join(["---"] * len(header)) + " |")
                for row in rows[1:]:
                    cells = [str(c or "").strip() for c in row]
                    lines.append("| " + " | ".join(cells) + " |")
                table_texts.append("\n".join(lines))
            except Exception as e:
                logger.debug(f"[Ingestion] Table extraction row error: {e}")
    except AttributeError:
        # find_tables() not available in older PyMuPDF versions
        logger.debug("[Ingestion] find_tables() not available — skipping table extraction")
    except Exception as e:
        logger.debug(f"[Ingestion] Table extraction error: {e}")

    return "\n\n".join(table_texts)


def load_pdf(path: Path, use_vision: bool = True) -> List[dict]:
    """
    Load PDF pages using 3-path classification:

    TEXT_ONLY         → PyMuPDF text only (fast, free)
    STRUCTURED_VISUAL → PyMuPDF text + find_tables() + llava-phi3 diagram description
    HANDWRITTEN       → llava-phi3 full transcription + diagram description

    Returns list of {text, page, has_diagram, diagram_image_path}.
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    from .vision import (
        PageType,
        analyze_pdf_visual_pages,
        classify_page,
        render_page_as_image,
    )

    # Run vision pre-scan: classifies pages and sends non-text pages to llava-phi3
    vision_results = {}
    if use_vision:
        try:
            vision_results = analyze_pdf_visual_pages(str(path), save_images=True)
        except Exception as e:
            logger.warning(
                f"[Ingestion] Vision pre-scan failed for '{path.name}' (non-fatal): {e}. "
                f"Falling back to text-only extraction."
            )

    doc = fitz.open(str(path))
    pages = []

    for page_num, page in enumerate(doc):
        page_1indexed = page_num + 1
        extracted_text = page.get_text("text")
        image_count = len(page.get_images())
        page_type = classify_page(extracted_text, image_count)

        if page_num in vision_results and vision_results[page_num].success:
            # Vision result available for this page
            result = vision_results[page_num]

            if page_type == PageType.HANDWRITTEN:
                # Handwritten: vision output is the primary content
                final_text = result.text.strip()
            else:
                # Structured visual: combine PyMuPDF text + table markdown + vision diagram description
                table_text = _extract_tables_as_text(page)
                parts = [p for p in [
                    extracted_text.strip(),
                    f"\n\n[Tables]\n{table_text}" if table_text else "",
                    f"\n\n[Visual Elements]\n{result.text}" if result.text else "",
                ] if p]
                final_text = "\n".join(parts).strip()

            if final_text:
                pages.append({
                    "text": final_text,
                    "page": page_1indexed,
                    "has_diagram": result.has_diagram,
                    "diagram_image_path": result.image_saved_path,
                })

        elif page_type == PageType.TEXT_ONLY or not use_vision:
            # Text-only page: straight PyMuPDF extraction + tables
            table_text = _extract_tables_as_text(page)
            parts = [p for p in [
                extracted_text.strip(),
                f"\n\n[Tables]\n{table_text}" if table_text else "",
            ] if p]
            final_text = "\n".join(parts).strip()
            if final_text:
                pages.append({
                    "text": final_text,
                    "page": page_1indexed,
                    "has_diagram": False,
                    "diagram_image_path": "",
                })
        else:
            # Vision was requested but failed for this page → fall back to text
            if extracted_text.strip():
                pages.append({
                    "text": extracted_text.strip(),
                    "page": page_1indexed,
                    "has_diagram": False,
                    "diagram_image_path": "",
                })

    doc.close()
    logger.info(f"[Ingestion] '{path.name}': {len(pages)} pages loaded")
    return pages


def load_pptx(path: Path) -> List[dict]:
    """Load PPTX slides using python-pptx. Each slide is one 'page'."""
    try:
        from pptx import Presentation
    except ImportError:
        raise ImportError("python-pptx not installed. Run: pip install python-pptx")

    prs = Presentation(str(path))
    pages = []
    for slide_num, slide in enumerate(prs.slides, start=1):
        texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                texts.append(shape.text.strip())
        if texts:
            pages.append({
                "text": "\n\n".join(texts),
                "page": slide_num,
                "has_diagram": False,
                "diagram_image_path": "",
            })
    return pages


def load_markdown(path: Path) -> List[dict]:
    """Load a markdown or plain text file as a single page."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [{"text": text, "page": 1, "has_diagram": False, "diagram_image_path": ""}]


def load_document(path: Path) -> List[dict]:
    """Dispatch to the correct loader based on file extension."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return load_pdf(path)
    elif ext == ".pptx":
        return load_pptx(path)
    elif ext in (".md", ".txt", ".rst"):
        return load_markdown(path)
    else:
        logger.warning(f"[Ingestion] Unsupported file type: {path.name} — skipping")
        return []


# ── Text Cleaner ──────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Clean extracted document text.
    - Normalize whitespace
    - Remove repeated header/footer patterns
    - Preserve math expressions
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove page number lines (e.g. "- 12 -", "Page 12", "12 |", "| 12")
    text = re.sub(r"\n\s*([\-|]\s*)?\d+\s*([\-|])?\s*\n", "\n", text)
    text = re.sub(r"\n\s*page\s+\d+\s*\n", "\n", text, flags=re.IGNORECASE)

    # Remove repeated whitespace within lines
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Reduce 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ── Main Ingestion Pipeline ───────────────────────────────────────────────────

class IngestionPipeline:
    """
    Full offline ingestion pipeline.

    Steps:
      1. Load all documents from source_dir
      2. Clean text
      3. Chunk using EducationalChunker
      4. Validate chunks (hard-fail gates)
      5. Exact deduplication
      6. Embed in batches via OpenAI
      7. Cosine deduplication against new + existing embeddings
      8. Bulk insert into KnowledgeChunk
      9. Link parent chunks (examples/mistakes → nearest procedure)
    """

    def __init__(self, dry_run: bool = False, show_chunks: bool = False, use_vision: bool = True):
        self.dry_run = dry_run
        self.show_chunks = show_chunks
        self.use_vision = use_vision
        self.chunker = EducationalChunker()
        self.topic_chunker = None  # set in run() if --topics-file provided

    def run(
        self,
        source_dir: str,
        topic_id: int,
        subject: str,
        index_version: str = "v1.0",
        concept_tag: str = "",
        difficulty: str = "medium",
        topics_file: str = "",
    ) -> dict:
        """
        Run the full ingestion pipeline for a directory of documents.

        Args:
            source_dir:    Path to directory containing PDF/PPT/MD files.
            topic_id:      Django Topic.id this content belongs to.
            subject:       Subject label ("CS", "Math", "Physics").
            index_version: Index version string ("v1.0").
            concept_tag:   Concept label override (if empty, uses filename).
            difficulty:    Default difficulty for all chunks.

        Returns:
            Stats dict with file/chunk counts and elapsed time.
        """
        from core.models import Topic

        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source path not found: {source_dir}")

        topic = Topic.objects.get(id=topic_id)

        stats = {
            "files_processed": 0,
            "chunks_produced": 0,
            "chunks_validated": 0,
            "chunks_inserted": 0,
            "chunks_skipped": 0,
            "start_time": time.perf_counter(),
        }

        # Accept both a single file and a directory
        supported_exts = {".pdf", ".pptx", ".md", ".txt", ".rst"}
        if source_path.is_file():
            files = [source_path] if source_path.suffix.lower() in supported_exts else []
        else:
            files = [f for f in source_path.rglob("*") if f.suffix.lower() in supported_exts]

        if not files:
            logger.warning(f"[Ingestion] No supported files found at: {source_dir}")
            return stats

        logger.info(f"[Ingestion] Starting pipeline: {len(files)} files, topic={topic.title}, subject={subject}")
        print(f"\n[DIR] Found {len(files)} file(s) to ingest", flush=True)

        # Load topic-guided chunker if topics file provided
        topics_data = None
        if topics_file:
            topics_path = Path(topics_file)
            if not topics_path.exists():
                raise FileNotFoundError(f"Topics file not found: {topics_file}")
            topics_data = json.loads(topics_path.read_text(encoding="utf-8"))
            from .chunker import TopicGuidedChunker
            self.topic_chunker = TopicGuidedChunker()
            total_topics = len(topics_data)
            total_subtopics = sum(len(t.get("subtopics", [])) for t in topics_data)
            print(f"[TOPICS] Topics file loaded: {total_topics} topics, {total_subtopics} subtopics", flush=True)

        all_candidates: List[ChunkCandidate] = []

        # ── Stage 1-4: Load → Clean → Chunk → Validate (with vision for PDFs) ──
        for file_idx, file_path in enumerate(files, 1):
            print(f"\n[FILE] [{file_idx}/{len(files)}] {file_path.name}", flush=True)
            print(   f"   [SCAN] Vision scanning pages...", flush=True)
            logger.info(f"[Ingestion] Loading: {file_path.name}")

            # load_pdf does the vision pre-scan internally for PDFs
            if file_path.suffix.lower() == ".pdf":
                pages = load_pdf(file_path, use_vision=self.use_vision)
            else:
                pages = load_document(file_path)

            if not pages:
                continue

            # Track per-page vision metadata (has_diagram, diagram_image_path)
            page_vision_meta = {
                p["page"]: {
                    "has_diagram": p.get("has_diagram", False),
                    "diagram_image_path": p.get("diagram_image_path", ""),
                }
                for p in pages
            }

            # Combine all pages into one document text with page markers
            full_text = "\n\n".join(
                f"[Page {p['page']}]\n{p['text']}" for p in pages
            )
            full_text = clean_text(full_text)

            tag = concept_tag or file_path.stem.replace("_", " ").replace("-", " ").title()

            if topics_data and self.topic_chunker:
                # ── Topic-guided chunking ──────────────────────────────────
                print(f"   [TOPICS] Using topic-guided chunking ({len(topics_data)} topics)...", flush=True)
                raw = self.topic_chunker.chunk_with_topics(
                    text=full_text,
                    topics=topics_data,
                    source_file=file_path.name,
                    difficulty=difficulty,
                )
            else:
                # ── Heuristic chunking (default) ──────────────────────────
                raw = self.chunker.chunk_document(
                    text=full_text,
                    source_file=file_path.name,
                    concept_tag=tag,
                    difficulty=difficulty,
                )

            # Assign page numbers and vision metadata by finding closest [Page N] marker
            self._assign_page_numbers(raw, pages)
            self._assign_vision_metadata(raw, page_vision_meta)

            # Validate
            valid = [c for c in raw if self.chunker.validate(c)]

            stats["chunks_produced"] += len(raw)
            stats["chunks_validated"] += len(valid)
            stats["files_processed"] += 1

            print(f"   [OK] {len(raw)} raw → {len(valid)} valid chunks", flush=True)
            logger.info(
                f"[Ingestion] {file_path.name}: "
                f"{len(raw)} raw → {len(valid)} valid chunks"
            )
            all_candidates.extend(valid)

        if not all_candidates:
            logger.warning("[Ingestion] No valid chunks produced — nothing to insert.")
            return stats

        # ── Stage 5: Exact deduplication ────────────────────────────────────
        all_candidates = self.chunker.deduplicate(all_candidates)

        if self.show_chunks:
            self._print_chunk_preview(all_candidates[:5])

        if self.dry_run:
            logger.info(f"[Ingestion] DRY RUN — would insert {len(all_candidates)} chunks. Skipping DB.")
            stats["chunks_inserted"] = 0
            stats["chunks_skipped"] = stats["chunks_produced"] - len(all_candidates)
            return stats

        # ── Stage 6: Embed ───────────────────────────────────────────────────
        print(f"\n[EMBED] Embedding {len(all_candidates)} chunks with nomic-embed-text...", flush=True)
        logger.info(f"[Ingestion] Embedding {len(all_candidates)} chunks...")
        texts = [c.text for c in all_candidates]
        embeddings = embed_batch(texts)

        # ── Stage 7: Cosine deduplication against existing DB chunks ─────────
        existing_embeddings = self._fetch_existing_embeddings(topic_id, index_version)
        all_candidates, embeddings = self.chunker.deduplicate_with_embeddings(
            all_candidates, embeddings, existing_embeddings, threshold=0.97
        )

        # ── Stage 8: Soft-deprecate old chunks for this topic+version ────────
        self._deprecate_old_chunks(topic_id, index_version)

        # ── Stage 9: Bulk insert ─────────────────────────────────────────────
        print(f"\n[SAVE] Inserting {len(all_candidates)} chunks into pgvector...", flush=True)
        inserted = self._bulk_insert(
            candidates=all_candidates,
            embeddings=embeddings,
            topic=topic,
            subject=subject,
            index_version=index_version,
        )

        stats["chunks_inserted"] = inserted
        stats["chunks_skipped"] = stats["chunks_produced"] - inserted
        stats["elapsed_s"] = time.perf_counter() - stats["start_time"]

        # ── Stage 10: Link parent chunks ─────────────────────────────────────
        print(f"[LINK] Linking parent chunks...", flush=True)
        self._link_parent_chunks(topic_id, index_version)

        logger.info(
            f"[Ingestion] Done: {inserted} chunks inserted, "
            f"{stats['chunks_skipped']} skipped, "
            f"{stats.get('elapsed_s', 0):.1f}s elapsed."
        )
        return stats

    def _assign_page_numbers(self, candidates: List[ChunkCandidate], pages: List[dict]):
        """Assign source_page to each candidate using [Page N] markers in text."""
        page_map = {p["page"]: p["text"][:100] for p in pages}
        current_page = 1

        for c in candidates:
            match = re.search(r"\[Page (\d+)\]", c.text)
            if match:
                c.source_page = int(match.group(1))
                c.text = re.sub(r"\[Page \d+\]\n?", "", c.text).strip()
            else:
                c.source_page = current_page

    def _assign_vision_metadata(
        self,
        candidates: List[ChunkCandidate],
        page_vision_meta: dict,
    ):
        """
        Propagate vision metadata (has_diagram, diagram_image_path) from
        page-level results down to individual ChunkCandidates.

        A chunk gets has_diagram=True if the page it came from contained diagrams.
        """
        for c in candidates:
            meta = page_vision_meta.get(c.source_page, {})
            c.has_diagram = meta.get("has_diagram", False)
            c.diagram_image_path = meta.get("diagram_image_path", "")

    def _fetch_existing_embeddings(self, topic_id: int, index_version: str) -> List[List[float]]:
        """Fetch embeddings of existing active chunks for cosine dedup."""
        existing = KnowledgeChunk.objects.filter(
            topic_id=topic_id,
            index_version=index_version,
            is_active=True,
        ).values_list("embedding", flat=True)
        return [list(e) for e in existing if e is not None]

    def _deprecate_old_chunks(self, topic_id: int, index_version: str):
        """Soft-deprecate all existing active chunks for this topic+version before re-inserting."""
        count = KnowledgeChunk.objects.filter(
            topic_id=topic_id,
            index_version=index_version,
            is_active=True,
        ).update(is_active=False)
        if count:
            logger.info(f"[Ingestion] Deprecated {count} existing chunks for topic={topic_id}")

    @transaction.atomic
    def _bulk_insert(
        self,
        candidates: List[ChunkCandidate],
        embeddings: List[List[float]],
        topic,
        subject: str,
        index_version: str,
    ) -> int:
        """Bulk insert KnowledgeChunk records atomically."""
        chunk_objects = []

        for candidate, embedding in zip(candidates, embeddings):
            chunk_objects.append(KnowledgeChunk(
                topic=topic,
                subject=subject,
                concept_tag=candidate.concept_tag,
                text=candidate.text,
                chunk_type=candidate.chunk_type,
                difficulty=candidate.difficulty,
                source_file=candidate.source_file,
                source_page=candidate.source_page or 0,
                chunk_index=candidate.chunk_index,
                formula_latex=candidate.formula_latex,
                formula_plain=candidate.formula_plain,
                has_diagram=getattr(candidate, 'has_diagram', False),
                diagram_image_path=getattr(candidate, 'diagram_image_path', ''),
                embedding=embedding,
                is_active=True,
                index_version=index_version,
                parent_chunk=None,
            ))

        KnowledgeChunk.objects.bulk_create(chunk_objects, batch_size=100)
        logger.info(f"[Ingestion] Inserted {len(chunk_objects)} chunks")
        return len(chunk_objects)

    def _link_parent_chunks(self, topic_id: int, index_version: str):
        """
        Link child chunks to their parent chunks.

        Two linking strategies:
        1. Topic-guided: sub-topic chunks (parent_hint stored via chunk_index ordering)
           → link non-concept chunks to nearest preceding concept chunk
           with the SAME concept_tag.
        2. Heuristic: example/mistake chunks → nearest preceding procedure chunk.
        """
        chunks = list(
            KnowledgeChunk.objects.filter(
                topic_id=topic_id,
                index_version=index_version,
                is_active=True,
            ).order_by("chunk_index")
        )

        # Group by concept_tag to find concept parents for topic-guided chunks
        concept_parents: dict = {}   # concept_tag → KnowledgeChunk (concept type)
        last_procedure: Optional[KnowledgeChunk] = None
        updated = 0

        for chunk in chunks:
            if chunk.chunk_type == "concept":
                # Register as the current concept parent for this tag
                concept_parents[chunk.concept_tag] = chunk

            elif chunk.chunk_type == "procedure":
                last_procedure = chunk
                # Also link to concept parent if same concept_tag exists
                parent = concept_parents.get(chunk.concept_tag)
                if parent and chunk.parent_chunk_id is None:
                    chunk.parent_chunk = parent
                    chunk.save(update_fields=["parent_chunk"])
                    updated += 1

            elif chunk.chunk_type in ("example", "mistake"):
                # Prefer last procedure; fall back to concept parent
                parent = last_procedure or concept_parents.get(chunk.concept_tag)
                if parent and chunk.parent_chunk_id is None:
                    chunk.parent_chunk = parent
                    chunk.save(update_fields=["parent_chunk"])
                    updated += 1

            else:
                # definition, rule, comparison, comparison → link to concept parent
                parent = concept_parents.get(chunk.concept_tag)
                if parent and chunk.parent_chunk_id is None:
                    chunk.parent_chunk = parent
                    chunk.save(update_fields=["parent_chunk"])
                    updated += 1

        if updated:
            logger.info(f"[Ingestion] Linked {updated} chunks to parents")
            print(f"   ✓ {updated} chunks linked to parent topics", flush=True)

    def _print_chunk_preview(self, candidates: List[ChunkCandidate]):
        """Print first N chunks to stdout for inspection (--show-chunks flag)."""
        print("\n" + "=" * 70)
        print("CHUNK PREVIEW (first 5 valid chunks)")
        print("=" * 70)
        for i, c in enumerate(candidates, 1):
            print(f"\n[{i}] type={c.chunk_type} | tag={c.concept_tag} | file={c.source_file}")
            print(f"    difficulty={c.difficulty} | page={c.source_page}")
            if c.formula_latex:
                print(f"    formula_latex: {c.formula_latex[:80]}")
                print(f"    formula_plain: {c.formula_plain[:80]}")
            print(f"    text ({len(c.text)} chars):\n    {c.text[:300]}...")
        print("=" * 70 + "\n")
