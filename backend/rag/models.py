"""
RAG Knowledge System — Django Models

KnowledgeChunk is the single source of truth for all retrievable knowledge.
Uses pgvector for cosine similarity search with HNSW index.

Embedding model: Google gemini-embedding-001 (768 dimensions)
SACRED RULE: This same model must be used for both ingestion and online query.
             Never change it without rebuilding the entire index.
"""

from django.db import models
from pgvector.django import VectorField
from core.models import Topic


class KnowledgeChunk(models.Model):
    """
    A single retrievable unit of educational knowledge.

    The `text` field is the ONLY field that gets embedded.
    It must be written in natural language — never JSON, LaTeX, or code.
    All other structured fields (formula_latex, formula_plain, etc.) are metadata.
    """

    CHUNK_TYPES = [
        ("definition", "Definition"),
        ("concept", "Concept / Intuition"),
        ("rule", "Rule / Law / Formula"),
        ("procedure", "Procedure / Method"),
        ("example", "Worked Example"),
        ("mistake", "Common Mistake"),
        ("comparison", "Comparison / Edge Case"),
    ]

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    # ── Ownership ─────────────────────────────────────────────────────────────
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="knowledge_chunks",
        help_text="Which syllabus topic this chunk belongs to.",
    )
    subject = models.CharField(
        max_length=50,
        help_text='e.g. "CS", "Math", "Physics"',
    )
    concept_tag = models.CharField(
        max_length=100,
        help_text='e.g. "Binary Search", "Newton\'s Second Law"',
    )

    # ── Content — embedding target ─────────────────────────────────────────────
    text = models.TextField(
        help_text=(
            "The chunk text written in natural language. "
            "THIS IS THE ONLY FIELD THAT GETS EMBEDDED. "
            "Do NOT put LaTeX, JSON, or code here — write it as plain English."
        )
    )
    chunk_type = models.CharField(
        max_length=20,
        choices=CHUNK_TYPES,
        default="concept",
        db_index=True,
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default="medium",
        db_index=True,
    )

    # ── Source provenance ──────────────────────────────────────────────────────
    source_file = models.CharField(
        max_length=255,
        blank=True,
        help_text='e.g. "binary_search_lecture.pdf"',
    )
    source_page = models.IntegerField(
        null=True,
        blank=True,
        help_text="Page number in the source document.",
    )
    chunk_index = models.IntegerField(
        default=0,
        help_text="Order of this chunk within its source document.",
    )

    # ── Parent-child relationship ──────────────────────────────────────────────
    parent_chunk = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_chunks",
        help_text=(
            "For examples and mistakes: link to the procedure/rule chunk they relate to. "
            "When a child is retrieved, its parent is co-retrieved and prepended."
        ),
    )

    # ── Formula fields (metadata only — never embedded) ───────────────────────
    formula_latex = models.TextField(
        blank=True,
        help_text="LaTeX representation for display in UI. Never embedded.",
    )
    formula_plain = models.TextField(
        blank=True,
        help_text="Plain-text formula for TTS (e.g. 'F equals m times a'). Never embedded.",
    )

    # ── Vector ────────────────────────────────────────────────────────────────
    embedding = VectorField(
        dimensions=768,
        help_text="Google gemini-embedding-001 vector. 768 dimensions.",
    )

    # ── Vision fields (set when chunk came from a visual/handwritten page) ────
    has_diagram = models.BooleanField(
        default=False,
        help_text="True if this chunk was produced from a page containing diagrams or drawings.",
    )
    diagram_image_path = models.CharField(
        max_length=500,
        blank=True,
        help_text=(
            "Path to the saved PNG of the source page (in media/rag_diagrams/). "
            "Used to optionally show the student the original diagram during retrieval."
        ),
    )

    # ── Operational ───────────────────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=(
            "Soft-delete flag. Set to False to deprecate a chunk without removing it. "
            "Only is_active=True chunks are returned by retrieval."
        ),
    )
    index_version = models.CharField(
        max_length=20,
        default="v2.0",
        db_index=True,
        help_text=(
            "Version of the embedding model/index used to produce this chunk. "
            "v2.0 = gemini-embedding-001 (768d). "
            "Query always targets a single version. Never mix versions."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["topic", "chunk_index"]
        verbose_name = "Knowledge Chunk"
        verbose_name_plural = "Knowledge Chunks"
        indexes = [
            models.Index(fields=["topic", "is_active", "index_version"], name="rag_topic_active_version_idx"),
            models.Index(fields=["chunk_type"], name="rag_chunk_type_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.chunk_type}] {self.concept_tag} — {self.text[:60]}..."
