import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.services import EmbeddingService, RAGService

def verify_rag():
    query = "What is binary search?"
    print(f"Query: {query}")
    
    # 1. Embed
    vector = EmbeddingService.get_embedding(query, task_type="retrieval_query")
    if not vector:
        print("Failed to generate embedding.")
        return

    # 2. Retrieve
    chunks = RAGService.get_context(vector)
    print(f"Retrieved {len(chunks)} chunks.")
    if not chunks:
        print("NO CHUNKS RETRIEVED. Check database and is_approved flags.")
    
    for c in chunks:
        print(f" - Chunk match: {c.content[:30]}... (Dist: {c.distance:.4f})")
        
    # 3. Answer
    print("Generating answer...")
    answer = RAGService.generate_answer(query, chunks)
    print("\n--- AI ANSWER ---")
    print(f"Raw Output: {answer}")
    print("-----------------")

if __name__ == "__main__":
    verify_rag()

