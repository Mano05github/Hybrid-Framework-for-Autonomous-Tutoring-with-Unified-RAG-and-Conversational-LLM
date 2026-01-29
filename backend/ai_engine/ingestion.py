from django.conf import settings
from .models import KnowledgeChunk
from .services import EmbeddingService
from core.models import Topic

class IngestionService:
    @staticmethod
    def ingest_text(text, topic_id, source_url="Manual Entry", is_scraped=False):
        """
        Ingests strict educational content.
        1. Chunks text (max 500 tokens).
        2. Generates embeddings.
        3. Saves to DB.
        
        CRITICAL: If is_scraped=True, forced is_approved=False.
        """
        chunks = IngestionService._chunk_text(text)
        saved_count = 0
        
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            print(f"Topic ID {topic_id} not found.")
            return 0

        for chunk_text in chunks:
            vector = EmbeddingService.get_embedding(chunk_text)
            if not vector:
                continue

            # Policy Enforcement
            approved_status = True  # Default for manual entry
            if is_scraped:
                approved_status = False  # SCRAPED CONTENT MUST BE APPROVED MANUALLY

            KnowledgeChunk.objects.create(
                topic=topic,
                content=chunk_text,
                embedding=vector,
                source_url=source_url,
                is_approved=approved_status
            )
            saved_count += 1
            
        return saved_count

    @staticmethod
    def _chunk_text(text, max_tokens=500):
        """
        Simple semantic chunking.
        For now, splits by double newline (paragraphs) and groups them.
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            # Rough token estimate: 1 word ~ 1.3 tokens. 500 tokens ~ 380 words.
            if len(current_chunk.split()) + len(p.split()) < 380:
                current_chunk += "\n\n" + p
            else:
                chunks.append(current_chunk.strip())
                current_chunk = p
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return [c for c in chunks if c.strip()]
