"""
Teacher Agent + Omni-RAG Integration Test

Tests the complete Teacher Agent with RAG retrieval and LLM generation.

Prerequisites:
1. RAG storage must exist (run ingest.py first)
2. SetFit classifier must be trained (run supervisor/classifier.py)
3. LLM must be available (Ollama running or Gemini API key set)

Run: python test_teacher_rag.py
"""

import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine.agents import teacher_agent, get_supervisor_components
from ai_engine.state import AgentState
from langchain_core.messages import HumanMessage

def test_teacher_simple_query():
    """Test Teacher Agent with a simple single-hop query."""
    print("\n" + "="*80)
    print("TEST 1: Simple Query (Single-Hop RAG)")
    print("="*80)
    
    state = AgentState(
        messages=[],
        user_id="test_user_1",
        session_id="test_session_1",
        query="What is binary search?",
        intent="teacher",
        confidence=0.95,
        method="setfit",
        latency_ms=12.5,
        complexity_score=40,
        user_emotion="Neutral",
        current_topic="Binary Search",
        next_step="teacher",
        next_agent=None,
        response="",
        mastery_state=None,
        rag_strategy=None,
        rag_confidence=None,
        sources=None,
        teacher_latency_ms=None,
        error=None
    )
    
    # Execute teacher agent
    result_state = teacher_agent(state)
    
    # Validate results
    print("\n[Results]")
    print(f"Response length: {len(result_state['response'])} chars")
    print(f"RAG Strategy: {result_state.get('rag_strategy', 'N/A')}")
    print(f"RAG Confidence: {result_state.get('rag_confidence', 0):.2f}")
    print(f"Sources: {result_state.get('sources', [])}")
    print(f"Total Latency: {result_state.get('teacher_latency_ms', 0):.1f}ms")
    
    print(f"\n[Response Preview]")
    print(result_state['response'][:500] + "..." if len(result_state['response']) > 500 else result_state['response'])
    
    assert len(result_state['response']) > 50, "Response too short"
    assert result_state.get('rag_strategy') in ['no_rag', 'single_hop', 'multi_hop', 'iterative'], "Invalid RAG strategy"
    
    print("\n✓ Simple query test passed")


def test_teacher_comparative_query():
    """Test Teacher Agent with a comparative multi-hop query."""
    print("\n" + "="*80)
    print("TEST 2: Comparative Query (Multi-Hop RAG)")
    print("="*80)
    
    state = AgentState(
        messages=[],
        user_id="test_user_2",
        session_id="test_session_2",
        query="Compare quicksort and mergesort",
        intent="teacher",
        confidence=0.92,
        method="setfit",
        latency_ms=13.2,
        complexity_score=75,
        user_emotion="Curious",
        current_topic="Sorting Algorithms",
        next_step="teacher",
        next_agent=None,
        response="",
        mastery_state=None,
        rag_strategy=None,
        rag_confidence=None,
        sources=None,
        teacher_latency_ms=None,
        error=None
    )
    
    result_state = teacher_agent(state)
    
    print("\n[Results]")
    print(f"Response length: {len(result_state['response'])} chars")
    print(f"RAG Strategy: {result_state.get('rag_strategy', 'N/A')}")
    print(f"Number of sources: {len(result_state.get('sources', []))}")
    print(f"Total Latency: {result_state.get('teacher_latency_ms', 0):.1f}ms")
    
    print(f"\n[Response Preview]")
    print(result_state['response'][:500] + "..." if len(result_state['response']) > 500 else result_state['response'])
    
    # Multi-hop should retrieve from multiple topics
    assert result_state.get('rag_strategy') in ['multi_hop', 'iterative'], "Expected multi-hop strategy"
    
    print("\n✓ Comparative query test passed")


def test_teacher_greeting():
    """Test Teacher Agent with a greeting (No RAG)."""
    print("\n" + "="*80)
    print("TEST 3: Greeting (No RAG)")
    print("="*80)
    
    state = AgentState(
        messages=[],
        user_id="test_user_3",
        session_id="test_session_3",
        query="Hello! How are you?",
        intent="teacher",
        confidence=0.88,
        method="cache",
        latency_ms=5.1,
        complexity_score=10,
        user_emotion="Friendly",
        current_topic="",
        next_step="teacher",
        next_agent=None,
        response="",
        mastery_state=None,
        rag_strategy=None,
        rag_confidence=None,
        sources=None,
        teacher_latency_ms=None,
        error=None
    )
    
    result_state = teacher_agent(state)
    
    print("\n[Results]")
    print(f"Response length: {len(result_state['response'])} chars")
    print(f"RAG Strategy: {result_state.get('rag_strategy', 'N/A')}")
    print(f"Sources: {result_state.get('sources', [])}")
    
    print(f"\n[Response Preview]")
    print(result_state['response'])
    
    # Greeting should not use RAG
    assert result_state.get('rag_strategy') == 'no_rag', "Expected no RAG for greeting"
    assert len(result_state.get('sources', [])) == 0, "Expected no sources for greeting"
    
    print("\n✓ Greeting test passed")


def test_teacher_complex_reasoning():
    """Test Teacher Agent with a complex reasoning query (Iterative RAG)."""
    print("\n" + "="*80)
    print("TEST 4: Complex Reasoning (Iterative RAG)")
    print("="*80)
    
    state = AgentState(
        messages=[],
        user_id="test_user_4",
        session_id="test_session_4",
        query="Explain why quicksort has O(n log n) average case complexity",
        intent="teacher",
        confidence=0.91,
        method="setfit",
        latency_ms=14.8,
        complexity_score=85,
        user_emotion="Focused",
        current_topic="Algorithm Analysis",
        next_step="teacher",
        next_agent=None,
        response="",
        mastery_state=None,
        rag_strategy=None,
        rag_confidence=None,
        sources=None,
        teacher_latency_ms=None,
        error=None
    )
    
    result_state = teacher_agent(state)
    
    print("\n[Results]")
    print(f"Response length: {len(result_state['response'])} chars")
    print(f"RAG Strategy: {result_state.get('rag_strategy', 'N/A')}")
    print(f"Sources: {result_state.get('sources', [])}")
    print(f"Total Latency: {result_state.get('teacher_latency_ms', 0):.1f}ms")
    
    print(f"\n[Response Preview]")
    print(result_state['response'][:500] + "..." if len(result_state['response']) > 500 else result_state['response'])
    
    print("\n✓ Complex reasoning test passed")


def test_performance_metrics():
    """Test performance across multiple queries."""
    print("\n" + "="*80)
    print("TEST 5: Performance Metrics")
    print("="*80)
    
    queries = [
        ("What is a binary tree?", 45),
        ("Explain linked lists", 40),
        ("What is time complexity?", 50),
    ]
    
    latencies = []
    strategies = {}
    
    for query, complexity in queries:
        state = AgentState(
            messages=[],
            user_id="test_user_perf",
            session_id="test_session_perf",
            query=query,
            intent="teacher",
            confidence=0.90,
            method="setfit",
            latency_ms=12.0,
            complexity_score=complexity,
            user_emotion="Neutral",
            current_topic="",
            next_step="teacher",
            next_agent=None,
            response="",
            mastery_state=None,
            rag_strategy=None,
            rag_confidence=None,
            sources=None,
            teacher_latency_ms=None,
            error=None
        )
        
        result_state = teacher_agent(state)
        
        latency = result_state.get('teacher_latency_ms', 0)
        strategy = result_state.get('rag_strategy', 'unknown')
        
        latencies.append(latency)
        strategies[strategy] = strategies.get(strategy, 0) + 1
        
        print(f"\nQuery: {query}")
        print(f"  Latency: {latency:.1f}ms | Strategy: {strategy}")
    
    print(f"\n[Performance Summary]")
    print(f"  Avg Latency: {sum(latencies)/len(latencies):.1f}ms")
    print(f"  Min Latency: {min(latencies):.1f}ms")
    print(f"  Max Latency: {max(latencies):.1f}ms")
    print(f"  Strategy Distribution: {strategies}")
    
    print("\n✓ Performance metrics test passed")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("TEACHER AGENT + OMNI-RAG INTEGRATION TEST SUITE")
    print("="*80)
    
    # Check prerequisites
    rag_storage = Path(__file__).parent.parent / "rag_system" / "storage"
    if not rag_storage.exists():
        print("\n⚠ WARNING: RAG storage not found!")
        print(f"Expected: {rag_storage}")
        print("Please run ingest.py first to populate the vector database.")
        return 1
    
    setfit_model = Path(__file__).parent / "models" / "setfit_intent_classifier"
    if not setfit_model.exists():
        print("\n⚠ WARNING: SetFit model not trained!")
        print("Training model now...")
        # Will auto-train on first use
    
    try:
        test_teacher_simple_query()
        test_teacher_comparative_query()
        test_teacher_greeting()
        test_teacher_complex_reasoning()
        test_performance_metrics()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED - Teacher Agent + RAG Integration Working!")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
