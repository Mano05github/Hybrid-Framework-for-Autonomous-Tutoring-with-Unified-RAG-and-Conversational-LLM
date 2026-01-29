"""
Test script for Gap 3 code sandbox implementation
Tests various scenarios: correct code, infinite loops, dangerous operations, etc.
Run from backend/tests/ with: python test_sandbox.py
"""
import asyncio
import sys
import os
import django

# Setup Django - go up one directory to backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.gaps.coder_engine import SocraticCoderEngine
from learning_session.models import CodingProblem


async def test_sandbox():
    """Test the sandboxed code execution"""
    engine = SocraticCoderEngine()
    
    print("=" * 60)
    print("TESTING GAP 3 CODE SANDBOX")
    print("=" * 60)
    
    # Test 1: Simple correct code
    print("\n[TEST 1] Simple addition function")
    code1 = """
def main(a, b):
    return a + b
"""
    result1 = await engine._execute_code_safely(code1, [5, 3])
    print(f"Input: [5, 3]")
    print(f"Result: {result1}")
    print(f"✓ Expected: 8, Got: {result1['output']}")
    
    # Test 2: List operations
    print("\n[TEST 2] List sum function")
    code2 = """
def main(numbers):
    return sum(numbers)
"""
    result2 = await engine._execute_code_safely(code2, [[1, 2, 3, 4, 5]])
    print(f"Input: [[1, 2, 3, 4, 5]]")
    print(f"Result: {result2}")
    print(f"✓ Expected: 15, Got: {result2['output']}")
    
    # Test 3: String manipulation
    print("\n[TEST 3] String reversal")
    code3 = """
def main(text):
    return text[::-1]
"""
    result3 = await engine._execute_code_safely(code3, ["hello"])
    print(f"Input: ['hello']")
    print(f"Result: {result3}")
    print(f"✓ Expected: 'olleh', Got: {result3['output']}")
    
    # Test 4: Syntax error
    print("\n[TEST 4] Syntax error handling")
    code4 = """
def main(x)
    return x * 2
"""
    result4 = await engine._execute_code_safely(code4, [10])
    print(f"Result: {result4}")
    print(f"✓ Should fail with compilation error: {not result4['success']}")
    
    # Test 5: Dangerous operation (should be blocked)
    print("\n[TEST 5] Dangerous operation - file access")
    code5 = """
def main():
    with open('/etc/passwd', 'r') as f:
        return f.read()
"""
    result5 = await engine._execute_code_safely(code5, [])
    print(f"Result: {result5}")
    print(f"✓ Should fail (no open() access): {not result5['success']}")
    
    # Test 6: Import blocking
    print("\n[TEST 6] Import blocking")
    code6 = """
import os
def main():
    return os.getcwd()
"""
    result6 = await engine._execute_code_safely(code6, [])
    print(f"Result: {result6}")
    print(f"✓ Should fail (no imports): {not result6['success']}")
    
    # Test 7: Infinite loop (timeout test) - WARNING: This will take 5+ seconds
    print("\n[TEST 7] Infinite loop timeout (will take 5+ seconds)")
    code7 = """
def main():
    while True:
        pass
"""
    result7 = await engine._execute_code_safely(code7, [])
    print(f"Result: {result7}")
    print(f"✓ Should timeout: {not result7['success'] and 'timeout' in result7.get('error', '').lower()}")
    
    # Test 8: Output comparison
    print("\n[TEST 8] Output comparison tests")
    print("  8.1: Integer equality")
    assert engine._compare_outputs(42, 42) == True
    print("  ✓ 42 == 42")
    
    print("  8.2: Float tolerance")
    assert engine._compare_outputs(3.14159, 3.14159001) == True
    print("  ✓ 3.14159 ≈ 3.14159001 (within tolerance)")
    
    print("  8.3: List equality")
    assert engine._compare_outputs([1, 2, 3], [1, 2, 3]) == True
    print("  ✓ [1, 2, 3] == [1, 2, 3]")
    
    print("  8.4: Nested list")
    assert engine._compare_outputs([[1, 2], [3, 4]], [[1, 2], [3, 4]]) == True
    print("  ✓ [[1, 2], [3, 4]] == [[1, 2], [3, 4]]")
    
    print("  8.5: Dict equality")
    assert engine._compare_outputs({'a': 1, 'b': 2}, {'b': 2, 'a': 1}) == True
    print("  ✓ {'a': 1, 'b': 2} == {'b': 2, 'a': 1}")
    
    print("\n" + "=" * 60)
    print("✅ ALL SANDBOX TESTS COMPLETED")
    print("=" * 60)
    
    # Test with a real problem from database (if exists)
    print("\n[BONUS] Testing with database problem (if exists)")
    try:
        # Check if we have any coding problems
        problem_count = await asyncio.to_thread(CodingProblem.objects.count)
        if problem_count > 0:
            problem = await asyncio.to_thread(lambda: CodingProblem.objects.first())
            print(f"\nFound problem: {problem.title}")
            print(f"Test cases: {len(problem.test_cases)}")
            
            # Create a sample correct solution for testing
            if problem.test_cases:
                test_case = problem.test_cases[0]
                print(f"First test case: input={test_case.get('input')}, expected={test_case.get('expected_output')}")
        else:
            print("No coding problems in database yet. Create some for full testing.")
    except Exception as e:
        print(f"Database test skipped: {e}")


if __name__ == "__main__":
    asyncio.run(test_sandbox())
