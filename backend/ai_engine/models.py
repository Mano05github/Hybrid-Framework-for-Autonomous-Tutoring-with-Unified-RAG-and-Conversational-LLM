from django.db import models
from pgvector.django import VectorField
from core.models import Topic

class KnowledgeChunk(models.Model):
    """
    Stores educational content chunks with their vector embeddings.
    Strictly tied to the syllabus (Topic) and requires approval.
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='knowledge_chunks')
    content = models.TextField(help_text="Educational content (max 500 tokens).")
    # Gemini text-embedding-004 uses 768 dimensions
    embedding = VectorField(dimensions=768, help_text="Gemini text-embedding-004 vector.")
    source_url = models.URLField(blank=True, help_text="Source URL if scraped.")
    is_approved = models.BooleanField(default=False, help_text="Must be True to be used in RAG.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic.title} - Chunk {self.id} ({'Approved' if self.is_approved else 'Draft'})"
