"""
RAG Vision — llava-phi3 via Ollama (fully offline)

3-path page classifier:
  TEXT_ONLY        → PyMuPDF text extraction, skip vision
  STRUCTURED_VISUAL → PyMuPDF text + find_tables() + llava-phi3 for diagrams only
  HANDWRITTEN       → llava-phi3 full transcription + diagram description

API:
    classify_page(text, image_count) -> PageType
    analyze_page(image_bytes, page_type, source_file, page_num) -> VisionResult
    analyze_pdf_visual_pages(pdf_path) -> dict[int, VisionResult]
"""

import base64
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
VISION_MODEL     = os.getenv("OLLAMA_VISION_MODEL", "llava-phi3")
OLLAMA_HOST      = os.getenv("OLLAMA_HOST", "http://localhost:11434")
TEXT_THRESHOLD   = 150     # chars below this → treat page as handwritten
MAX_RETRIES      = 3
BASE_BACKOFF     = 2.0     # seconds


class PageType(Enum):
    TEXT_ONLY         = "text_only"         # machine text, no images → skip vision
    STRUCTURED_VISUAL = "structured_visual" # text + embedded diagrams/tables
    HANDWRITTEN       = "handwritten"       # low/no machine text, human handwriting


# ── Prompts (one per page type) ───────────────────────────────────────────────
_PROMPT_STRUCTURED = """You are analyzing a page from educational notes or a textbook.
This page contains text AND diagrams, workflows, or visual elements.

Your task:
1. DO NOT re-transcribe the text — that is already extracted separately.
2. Focus ONLY on the visual elements: diagrams, flowcharts, workflows, tables drawn as images.
3. For each visual element, describe in plain English:
   - What concept it illustrates
   - What the arrows, nodes, boxes, or labels mean
   - Any step-by-step process shown

Write your description in plain paragraphs. No bullet points required.
Be thorough — this description will be used for semantic search."""

_PROMPT_HANDWRITTEN = """You are analyzing a page of handwritten educational notes.

Your task:
1. Transcribe ALL handwritten text exactly as written (fix obvious spelling where clear).
2. For every diagram, sketch, flowchart, or drawing:
   - Describe what it shows in plain English
   - Explain the concept it illustrates
   - Describe relationships shown by arrows or labels
   - If it shows a step-by-step process, describe each step in order

Write formulas in plain English (e.g. "F equals m times a" not LaTeX).
Be thorough — your output is the only source of content from this page."""


@dataclass
class VisionResult:
    text: str                    # Natural language content ready for chunking
    page_type: PageType = PageType.TEXT_ONLY
    has_diagram: bool = False
    image_saved_path: str = ""
    success: bool = True
    error: str = ""


# ── Page classifier ───────────────────────────────────────────────────────────

def classify_page(extracted_text: str, image_count: int) -> PageType:
    """
    Classify a PDF page into one of 3 processing paths.

    Args:
        extracted_text: Raw text from PyMuPDF get_text()
        image_count:    Number of embedded images on the page
    """
    text_len = len(extracted_text.strip())

    if text_len < TEXT_THRESHOLD:
        return PageType.HANDWRITTEN

    if image_count > 0:
        return PageType.STRUCTURED_VISUAL

    return PageType.TEXT_ONLY


# ── Image utilities ───────────────────────────────────────────────────────────

def render_page_as_image(pdf_path: str, page_num: int, dpi: int = 150) -> bytes:
    """Render a PDF page as PNG bytes using PyMuPDF."""
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    image_bytes = pix.tobytes("png")
    doc.close()
    return image_bytes


def save_page_image(image_bytes: bytes, source_file: str, page_num: int) -> str:
    """Save a page PNG to media/rag_diagrams/ for later display to students."""
    media_dir = Path("media") / "rag_diagrams"
    media_dir.mkdir(parents=True, exist_ok=True)
    base = Path(source_file).stem.replace(" ", "_")
    filename = f"{base}_page{page_num + 1}.png"
    save_path = media_dir / filename
    save_path.write_bytes(image_bytes)
    return str(save_path)


# ── Core vision call ──────────────────────────────────────────────────────────

def analyze_page(
    image_bytes: bytes,
    page_type: PageType,
    source_file: str = "",
    page_num: int = 0,
    save_image: bool = True,
) -> VisionResult:
    """
    Send a page image to llava-phi3 via Ollama and return a plain text description.

    Only called for STRUCTURED_VISUAL and HANDWRITTEN pages.
    TEXT_ONLY pages should never be sent here.
    """
    try:
        import ollama
    except ImportError:
        raise ImportError("ollama not installed. Run: pip install ollama")

    if page_type == PageType.TEXT_ONLY:
        return VisionResult(text="", page_type=page_type, success=True)

    prompt = (
        _PROMPT_HANDWRITTEN
        if page_type == PageType.HANDWRITTEN
        else _PROMPT_STRUCTURED
    )

    # Save image for diagram display to students later
    image_saved_path = ""
    if save_image and source_file and page_type != PageType.TEXT_ONLY:
        try:
            image_saved_path = save_page_image(image_bytes, source_file, page_num)
        except Exception as e:
            logger.warning(f"[Vision] Could not save page image: {e}")

    # Encode image as base64 for Ollama
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.perf_counter()
            response = ollama.chat(
                model=VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }],
                options={"temperature": 0.1},   # low temp for factual transcription
            )
            latency_ms = (time.perf_counter() - t0) * 1000
            raw_text = response["message"]["content"].strip()

            logger.info(
                f"[Vision] Page {page_num + 1} ({page_type.value}) of "
                f"'{source_file}' analyzed in {latency_ms:.0f}ms"
            )

            has_diagram = page_type in (PageType.STRUCTURED_VISUAL, PageType.HANDWRITTEN)

            return VisionResult(
                text=raw_text,
                page_type=page_type,
                has_diagram=has_diagram,
                image_saved_path=image_saved_path,
                success=True,
            )

        except Exception as e:
            wait = BASE_BACKOFF * attempt
            logger.warning(
                f"[Vision] Attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                f"Retrying in {wait:.0f}s..."
            )
            time.sleep(wait)
            last_error = e

    return VisionResult(
        text="",
        page_type=page_type,
        success=False,
        error=f"Vision failed after {MAX_RETRIES} attempts: {last_error}",
    )


# ── PDF-level scanner ─────────────────────────────────────────────────────────

def analyze_pdf_visual_pages(
    pdf_path: str,
    save_images: bool = True,
) -> Dict[int, VisionResult]:
    """
    Scan all pages of a PDF. Classify each page and run vision only on
    STRUCTURED_VISUAL and HANDWRITTEN pages.

    Returns: dict[page_num (0-indexed)] -> VisionResult
             Only non-TEXT_ONLY pages are included.
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    doc = fitz.open(pdf_path)
    results: Dict[int, VisionResult] = {}
    source_file = Path(pdf_path).name

    counts = {"text_only": 0, "structured": 0, "handwritten": 0, "failed": 0}

    for page_num in range(len(doc)):
        page = doc[page_num]
        extracted_text = page.get_text("text")
        image_count = len(page.get_images())
        page_type = classify_page(extracted_text, image_count)

        if page_type == PageType.TEXT_ONLY:
            counts["text_only"] += 1
            continue

        # Render and analyze visual/handwritten page
        image_bytes = render_page_as_image(pdf_path, page_num, dpi=150)
        result = analyze_page(
            image_bytes=image_bytes,
            page_type=page_type,
            source_file=source_file,
            page_num=page_num,
            save_image=save_images,
        )

        if result.success and result.text:
            results[page_num] = result
            if page_type == PageType.STRUCTURED_VISUAL:
                counts["structured"] += 1
            else:
                counts["handwritten"] += 1
        else:
            counts["failed"] += 1
            logger.error(
                f"[Vision] Page {page_num + 1} failed: {result.error}"
            )

    doc.close()
    logger.info(
        f"[Vision] '{source_file}' complete: "
        f"{counts['text_only']} text-only (skipped), "
        f"{counts['structured']} structured, "
        f"{counts['handwritten']} handwritten, "
        f"{counts['failed']} failed"
    )
    return results
