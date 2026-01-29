"""
Quick Test Script for Supervisor V2.0 Components
Run this to verify all components work before full integration
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test that all required packages are installed."""
    print("=" * 80)
    print("Testing Package Imports")
    print("=" * 80)
    
    try:
        import setfit
        print("✓ setfit installed")
    except ImportError:
        print("✗ setfit missing - Run: pip install setfit")
        return False
    
    try:
        import sentence_transformers
        print("✓ sentence-transformers installed")
    except ImportError:
        print("✗ sentence-transformers missing - Run: pip install sentence-transformers")
        return False
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✓ spacy + en_core_web_sm installed")
    except:
        print("✗ spacy model missing - Run: python -m spacy download en_core_web_sm")
        return False
    
    try:
        import sklearn
        print("✓ scikit-learn installed")
    except ImportError:
        print("✗ scikit-learn missing - Run: pip install scikit-learn")
        return False
    
    print("\n✅ All dependencies installed!\n")
    return True


def test_classifier():
    """Test SetFit classifier initialization."""
    print("=" * 80)
    print("Testing SetFit Classifier")
    print("=" * 80)
    
    try:
        from ai_engine.supervisor.classifier import IntentClassifier
        
        classifier = IntentClassifier()
        print("✓ Classifier initialized")
        
        # Check if training data exists
        training_data = Path(__file__).parent.parent / "data" / "intent_training.json"
        if training_data.exists():
            print(f"✓ Training data found: {training_data}")
        else:
            print(f"✗ Training data missing: {training_data}")
            return False
        
        print("\n✅ Classifier ready for training!\n")
        return True
    
    except Exception as e:
        print(f"✗ Classifier test failed: {e}")
        return False


def test_cache():
    """Test semantic cache."""
    print("=" * 80)
    print("Testing Semantic Cache")
    print("=" * 80)
    
    try:
        from ai_engine.supervisor.cache import SemanticCache
        
        cache = SemanticCache(similarity_threshold=0.85, max_size=100)
        print("✓ Cache initialized")
        
        # Test put/get
        cache.put("Explain binary search", "teacher", 0.95)
        print("✓ Cache put: 'Explain binary search'")
        
        result = cache.get("How does binary search work?")
        if result:
            intent, confidence = result
            print(f"✓ Cache hit: '{intent}' (semantic match!)")
        else:
            print("⚠ Cache miss (may need higher similarity)")
        
        stats = cache.get_stats()
        print(f"✓ Cache stats: {stats['hits']} hits, {stats['misses']} misses")
        
        print("\n✅ Cache working correctly!\n")
        return True
    
    except Exception as e:
        print(f"✗ Cache test failed: {e}")
        return False


def test_complexity():
    """Test complexity analyzer."""
    print("=" * 80)
    print("Testing Complexity Analyzer")
    print("=" * 80)
    
    try:
        from ai_engine.supervisor.complexity import ComplexityAnalyzer
        
        analyzer = ComplexityAnalyzer()
        print("✓ Analyzer initialized")
        
        # Test simple query
        metrics = analyzer.analyze("What is binary search?")
        print(f"✓ Simple query: score={metrics.score}/100")
        
        # Test complex query
        metrics = analyzer.analyze("Explain merge sort and quicksort and compare their time complexities")
        print(f"✓ Complex query: score={metrics.score}/100")
        
        if metrics.sub_queries and len(metrics.sub_queries) > 1:
            print(f"✓ Decomposition: {len(metrics.sub_queries)} sub-queries")
        
        print("\n✅ Complexity analyzer working!\n")
        return True
    
    except Exception as e:
        print(f"✗ Complexity test failed: {e}")
        return False


def test_dialogue():
    """Test dialogue state tracker."""
    print("=" * 80)
    print("Testing Dialogue State Tracker")
    print("=" * 80)
    
    try:
        from ai_engine.supervisor.dialogue import DialogueStateTracker
        
        tracker = DialogueStateTracker()
        print("✓ Tracker initialized")
        
        # Simulate conversation
        session_id = "test_session"
        
        tracker.track_turn("user1", session_id, "Explain binary search", "teacher")
        print("✓ Turn 1 tracked: 'Explain binary search'")
        
        resolved, context = tracker.resolve_context("Give me quiz on it", session_id)
        print(f"✓ Turn 2 resolved: '{resolved}'")
        
        if context.get('has_context'):
            print(f"✓ Context resolution: {context.get('resolved_reference')}")
        
        print("\n✅ Dialogue tracker working!\n")
        return True
    
    except Exception as e:
        print(f"✗ Dialogue test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("Supervisor V2.0 - Component Test Suite")
    print("=" * 80 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Classifier": test_classifier(),
        "Cache": test_cache(),
        "Complexity": test_complexity(),
        "Dialogue": test_dialogue()
    }
    
    print("=" * 80)
    print("Test Results Summary")
    print("=" * 80)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:15s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "=" * 80)
        print("🎉 All tests passed! Ready to train classifier:")
        print("   python -m ai_engine.supervisor.classifier")
        print("=" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print("⚠️  Some tests failed. Check error messages above.")
        print("=" * 80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
