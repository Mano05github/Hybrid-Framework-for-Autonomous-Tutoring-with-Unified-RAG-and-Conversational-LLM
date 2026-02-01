"""
Knowledge Base Verification Script
Run: python verify_knowledge_base.py
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.models import KnowledgeChunk
from core.models import Topic


def verify_knowledge_base():
    """Verify knowledge base is populated and ready for RAG."""
    
    print("=" * 80)
    print("KNOWLEDGE BASE VERIFICATION")
    print("=" * 80)
    
    # Check Topics
    topics = Topic.objects.all()
    print(f"\n📚 Topics: {topics.count()}")
    for topic in topics[:10]:
        print(f"   - {topic.title} ({topic.subject.name if topic.subject else 'No Subject'})")
    
    if topics.count() > 10:
        print(f"   ... and {topics.count() - 10} more")
    
    # Check Knowledge Chunks
    total_chunks = KnowledgeChunk.objects.count()
    approved_chunks = KnowledgeChunk.objects.filter(is_approved=True).count()
    pending_chunks = total_chunks - approved_chunks
    
    print(f"\n📦 Knowledge Chunks:")
    print(f"   Total:    {total_chunks}")
    print(f"   Approved: {approved_chunks}")
    print(f"   Pending:  {pending_chunks}")
    
    # Check embeddings
    chunks_with_embeddings = KnowledgeChunk.objects.exclude(embedding__isnull=True).count()
    print(f"   With embeddings: {chunks_with_embeddings}")
    
    # Sample approved chunk
    if approved_chunks > 0:
        sample_chunk = KnowledgeChunk.objects.filter(is_approved=True).first()
        print(f"\n✅ Sample Approved Chunk:")
        print(f"   Topic: {sample_chunk.topic.title if sample_chunk.topic else 'N/A'}")
        print(f"   Content: {sample_chunk.content[:200]}...")
        
        # Safe embedding check
        try:
            embedding_dim = len(sample_chunk.embedding) if sample_chunk.embedding is not None else 0
            print(f"   Embedding: {embedding_dim} dimensions")
        except:
            print(f"   Embedding: Present (array type)")
    
    # Status assessment
    print(f"\n{'=' * 80}")
    if approved_chunks == 0:
        print("❌ STATUS: NO APPROVED CHUNKS")
        print("\nAction Required:")
        print("1. Run ingestion script: python manage.py shell < ingest_pdf.py")
        print("2. Or approve pending chunks via Django admin: /admin/ai_engine/knowledgechunk/")
    elif approved_chunks < 10:
        print("⚠️ STATUS: LOW CONTENT")
        print(f"\nYou have only {approved_chunks} approved chunks.")
        print("Recommendation: Add more educational content for better RAG performance.")
    else:
        print("✅ STATUS: READY FOR RAG")
        print(f"\nYour knowledge base has {approved_chunks} approved chunks.")
        print("The teacher agent can now retrieve relevant content!")
    
    print("=" * 80)


if __name__ == "__main__":
    verify_knowledge_base()
