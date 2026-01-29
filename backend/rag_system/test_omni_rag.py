"""
Omni-RAG Test Suite

Tests all Omni-RAG components:
1. HybridRetriever (Vector + BM25 + Re-ranking)
2. OmniRAGOrchestrator (Adaptive routing)
3. CriticAgent (Self-correction)
4. Query strategies (No RAG, Single-Hop, Multi-Hop, Iterative)

Run: python test_omni_rag.py
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system import (
    HybridRetriever,
    OmniRAGOrchestrator,
    CriticAgent,
    QueryAnalyzer,
    RAGStrategy,
    get_omni_rag
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_hybrid_retriever():
    """Test HybridRetriever with vector + BM25 + re-ranking."""
    print("\n" + "="*80)
    print("TEST 1: Hybrid Retriever (Vector + BM25 + Re-Ranking)")
    print("="*80)
    
    retriever = HybridRetriever(
        vector_weight=0.5,
        bm25_weight=0.5,
        use_reranker=True,
        top_k=10,
        final_k=3
    )
    
    # Test queries
    test_queries = [
        "What is binary search?",
        "Explain time complexity of quicksort",
        "How does a binary tree work?"
    ]
    
    for query in test_queries:
        print(f"\n[Query] {query}")
        print("-" * 80)
        
        # Test vector search
        results = retriever.retrieve(query, k=3, method="vector")
        print(f"[Vector Search] Retrieved {len(results)} results")
        for r in results[:2]:
            print(f"  - {r.source} (score: {r.score:.3f}): {r.content[:100]}...")
        
        # Test hybrid search
        results = retriever.retrieve(query, k=3, method="hybrid")
        print(f"\n[Hybrid Search] Retrieved {len(results)} results")
        for r in results[:2]:
            print(f"  - {r.source} (score: {r.score:.3f}): {r.content[:100]}...")
        
        # Test context string
        context = retriever.get_context_string(query, k=2, compress=False)
        print(f"\n[Context String] Length: {len(context)} chars")
    
    print("\n✓ Hybrid Retriever test completed")


def test_query_analyzer():
    """Test QueryAnalyzer for strategy detection."""
    print("\n" + "="*80)
    print("TEST 2: Query Analyzer (Strategy Detection)")
    print("="*80)
    
    analyzer = QueryAnalyzer()
    
    test_cases = [
        ("Hello, how are you?", RAGStrategy.NO_RAG),
        ("What is a binary tree?", RAGStrategy.SINGLE_HOP),
        ("Compare quicksort vs mergesort", RAGStrategy.MULTI_HOP),
        ("Explain why quicksort is O(n log n)", RAGStrategy.ITERATIVE),
    ]
    
    for query, expected_strategy in test_cases:
        rag_query = analyzer.analyze(query, complexity_score=50)
        
        status = "✓" if rag_query.strategy == expected_strategy else "✗"
        print(f"\n{status} Query: {query}")
        print(f"  Strategy: {rag_query.strategy.value} (expected: {expected_strategy.value})")
        print(f"  Complexity: {rag_query.complexity_score}")
        if rag_query.sub_queries:
            print(f"  Sub-queries: {rag_query.sub_queries}")
    
    print("\n✓ Query Analyzer test completed")


def test_omni_rag_orchestrator():
    """Test OmniRAGOrchestrator with adaptive routing."""
    print("\n" + "="*80)
    print("TEST 3: Omni-RAG Orchestrator (Adaptive Routing)")
    print("="*80)
    
    orchestrator = get_omni_rag()
    
    test_queries = [
        ("Hello!", RAGStrategy.NO_RAG),
        ("What is binary search?", RAGStrategy.SINGLE_HOP),
        ("Compare binary search vs linear search", RAGStrategy.MULTI_HOP),
        ("Explain how quicksort time complexity is derived", RAGStrategy.ITERATIVE),
    ]
    
    for query, expected_strategy in test_queries:
        print(f"\n[Query] {query}")
        print("-" * 80)
        
        response = orchestrator.retrieve(query, complexity_score=60)
        
        print(f"Strategy: {response.strategy.value} (expected: {expected_strategy.value})")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Context chunks: {len(response.context_used)}")
        print(f"Sources: {response.sources}")
        
        if response.context_used:
            print(f"\nTop result preview:")
            print(f"  {response.context_used[0].content[:150]}...")
        
        # Format for LLM
        llm_context = orchestrator.format_context_for_llm(response)
        print(f"\nLLM Context length: {len(llm_context)} chars")
    
    print("\n✓ Omni-RAG Orchestrator test completed")


def test_multi_hop_rag():
    """Test Multi-Hop RAG for comparative queries."""
    print("\n" + "="*80)
    print("TEST 4: Multi-Hop RAG (Comparative Queries)")
    print("="*80)
    
    orchestrator = get_omni_rag()
    
    comparative_queries = [
        "Compare quicksort and mergesort",
        "What's the difference between stack and queue?",
        "Binary tree vs Binary search tree"
    ]
    
    for query in comparative_queries:
        print(f"\n[Query] {query}")
        print("-" * 80)
        
        response = orchestrator.retrieve(query)
        
        print(f"Strategy: {response.strategy.value}")
        print(f"Context chunks: {len(response.context_used)}")
        print(f"Unique sources: {len(response.sources)}")
        print(f"Sources: {response.sources}")
        
        # Show chunks from different sources
        sources_shown = set()
        for result in response.context_used[:4]:
            if result.source not in sources_shown:
                print(f"\n  [{result.source}] {result.content[:120]}...")
                sources_shown.add(result.source)
    
    print("\n✓ Multi-Hop RAG test completed")


def test_critic_agent():
    """Test CriticAgent for hallucination detection."""
    print("\n" + "="*80)
    print("TEST 5: Critic Agent (Self-Correction)")
    print("="*80)
    
    critic = CriticAgent()
    orchestrator = get_omni_rag()
    
    # Get some context first
    query = "What is binary search?"
    response = orchestrator.retrieve(query)
    
    if not response.context_used:
        print("⚠ No context retrieved, skipping critic test")
        return
    
    # Test cases
    test_answers = [
        ("Binary search is a divide-and-conquer algorithm that searches sorted arrays by repeatedly dividing the search interval in half.", True),
        ("Binary search works on unsorted arrays using bubble sort first.", False),
        ("The sky is blue and grass is green.", False),
    ]
    
    for answer, should_be_valid in test_answers:
        print(f"\n[Answer] {answer[:80]}...")
        
        is_valid, confidence, feedback = critic.validate_response(
            query=query,
            answer=answer,
            context=response.context_used,
            threshold=0.3
        )
        
        status = "✓" if is_valid == should_be_valid else "✗"
        print(f"{status} Valid: {is_valid} | Confidence: {confidence:.2f}")
        print(f"  Feedback: {feedback}")
    
    print("\n✓ Critic Agent test completed")


def test_performance_metrics():
    """Test performance and latency metrics."""
    print("\n" + "="*80)
    print("TEST 6: Performance Metrics")
    print("="*80)
    
    import time
    
    orchestrator = get_omni_rag()
    
    queries = [
        "What is binary search?",
        "Compare quicksort vs mergesort",
        "Explain time complexity"
    ]
    
    latencies = []
    
    for query in queries:
        start = time.perf_counter()
        response = orchestrator.retrieve(query)
        latency = (time.perf_counter() - start) * 1000
        
        latencies.append(latency)
        
        print(f"\n[Query] {query}")
        print(f"  Latency: {latency:.1f}ms")
        print(f"  Strategy: {response.strategy.value}")
        print(f"  Results: {len(response.context_used)}")
    
    print(f"\n[Summary]")
    print(f"  Avg Latency: {sum(latencies)/len(latencies):.1f}ms")
    print(f"  Min Latency: {min(latencies):.1f}ms")
    print(f"  Max Latency: {max(latencies):.1f}ms")
    
    print("\n✓ Performance metrics test completed")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("OMNI-RAG TEST SUITE")
    print("Testing: Hybrid Retrieval, Adaptive Routing, Self-Correction")
    print("="*80)
    
    try:
        # Check if storage exists
        storage_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "storage"
        )
        
        if not os.path.exists(storage_path):
            print(f"\n⚠ WARNING: RAG storage not found at {storage_path}")
            print("Please run ingest.py first to populate the vector database.")
            print("\nSkipping tests that require data...")
            
            # Only run tests that don't need data
            test_query_analyzer()
            return
        
        # Run all tests
        test_hybrid_retriever()
        test_query_analyzer()
        test_omni_rag_orchestrator()
        test_multi_hop_rag()
        test_critic_agent()
        test_performance_metrics()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ Test suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
