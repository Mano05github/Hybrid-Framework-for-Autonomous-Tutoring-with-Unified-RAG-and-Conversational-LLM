"""
Test script for Gap 3: Socratic Coder Agent implementation
Run with: python test_gap3.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import asyncio
from asgiref.sync import sync_to_async
from ai_engine.gaps.coder_engine import SocraticCoderEngine
from learning_session.models import CodingProblem, CodeSubmission, StudentCodingProfile
from users.models import User


async def test_syntax_error():
    """Test 1: Syntax error detection"""
    print("\n" + "="*60)
    print("TEST 1: Syntax Error Detection")
    print("="*60)
    
    engine = SocraticCoderEngine()
    
    # Get or create test user
    user, _ = await sync_to_async(User.objects.get_or_create)(
        username='test_student',
        defaults={'email': 'test@example.com', 'is_student': True}
    )
    
    # Get problem
    problem = await sync_to_async(CodingProblem.objects.first)()
    
    # Code with syntax error
    bad_code = """
def binary_search(arr, target
    left = 0
    right = len(arr) - 1
"""
    
    result = await engine.analyze_code_submission(
        user_id=user.id,
        problem_id=problem.id,
        code=bad_code,
        time_spent=30,
        emotion_valence=0.0
    )
    
    print(f"✓ Error Type: {result['analysis']['error_type']}")
    print(f"✓ Error Details: {result['analysis']['error_details']}")
    print(f"✓ Hint Level: {result['hint_decision']['hint_level']}")
    print(f"✓ Hint Text: {result['hint_text'][:100]}...")
    print(f"✓ Is Correct: {result['is_correct']}")
    
    assert result['analysis']['error_type'] == 'syntax', "Should detect syntax error"
    print("\n✅ TEST 1 PASSED: Syntax error detected correctly")


async def test_logic_error():
    """Test 2: Logic error detection"""
    print("\n" + "="*60)
    print("TEST 2: Logic Error Detection (Off-by-One)")
    print("="*60)
    
    engine = SocraticCoderEngine()
    user = await sync_to_async(User.objects.get)(username='test_student')
    problem = await sync_to_async(CodingProblem.objects.first)()
    
    # Code with off-by-one error
    logic_code = """
def binary_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
"""
    
    result = await engine.analyze_code_submission(
        user_id=user.id,
        problem_id=problem.id,
        code=logic_code,
        time_spent=60,
        emotion_valence=-0.2
    )
    
    print(f"✓ Error Type: {result['analysis']['error_type']}")
    print(f"✓ Error Details: {result['analysis']['error_details']}")
    print(f"✓ Hint Level: {result['hint_decision']['hint_level']}")
    print(f"✓ Hint Text: {result['hint_text'][:100]}...")
    
    assert result['analysis']['error_type'] == 'logic', "Should detect logic error"
    print("\n✅ TEST 2 PASSED: Logic error detected correctly")


async def test_struggle_detection():
    """Test 3: Struggle detection with high idle time"""
    print("\n" + "="*60)
    print("TEST 3: Struggle Detection (High Idle Time)")
    print("="*60)
    
    engine = SocraticCoderEngine()
    user = await sync_to_async(User.objects.get)(username='test_student')
    problem = await sync_to_async(CodingProblem.objects.first)()
    
    # Submit multiple times to simulate struggle
    code = """
def binary_search(arr, target):
    left = 0
    right = len(arr) - 1
    # Not sure what to do next
"""
    
    # First submission
    await engine.analyze_code_submission(
        user_id=user.id,
        problem_id=problem.id,
        code=code,
        time_spent=150,  # High idle time
        emotion_valence=-0.4  # Some frustration
    )
    
    # Second submission (should detect higher struggle)
    result = await engine.analyze_code_submission(
        user_id=user.id,
        problem_id=problem.id,
        code=code,
        time_spent=180,  # Even higher
        emotion_valence=-0.6  # More frustration
    )
    
    print(f"✓ Struggle Score: {result['hint_decision']['struggle_score']:.2f}")
    print(f"✓ Should Offer Hint: {result['hint_decision']['should_offer']}")
    print(f"✓ Hint Level: {result['hint_decision']['hint_level']}")
    print(f"✓ Reason: {result['hint_decision']['reason']}")
    
    assert result['hint_decision']['struggle_score'] > 0.6, "Should detect high struggle"
    assert result['hint_decision']['should_offer'], "Should offer hint"
    print("\n✅ TEST 3 PASSED: Struggle detection working correctly")


async def test_hint_levels():
    """Test 4: Different hint levels"""
    print("\n" + "="*60)
    print("TEST 4: Hint Level Progression")
    print("="*60)
    
    engine = SocraticCoderEngine()
    user = await sync_to_async(User.objects.get)(username='test_student')
    problem = await sync_to_async(CodingProblem.objects.first)()
    
    # Create student profile
    profile, _ = await sync_to_async(StudentCodingProfile.objects.get_or_create)(
        user=user,
        defaults={
            'skill_level': 'beginner',
            'avg_hint_level': 3.0,
            'quick_learner': False
        }
    )
    
    # Test with syntax error (should get level 4)
    syntax_code = "def test(\nprint('hi')"
    result1 = await engine.analyze_code_submission(
        user_id=user.id,
        problem_id=problem.id,
        code=syntax_code,
        time_spent=100,
        emotion_valence=-0.5
    )
    
    print(f"✓ Syntax Error → Hint Level: {result1['hint_decision']['hint_level']}")
    
    # Update profile to quick learner
    profile.quick_learner = True
    await sync_to_async(profile.save)()
    
    # Test again (should get lower level)
    result2 = await engine.analyze_code_submission(
        user_id=user.id,
        problem_id=problem.id,
        code=syntax_code,
        time_spent=100,
        emotion_valence=-0.5
    )
    
    print(f"✓ Quick Learner → Hint Level: {result2['hint_decision']['hint_level']}")
    
    assert result2['hint_decision']['hint_level'] < result1['hint_decision']['hint_level'], \
        "Quick learners should get lower hint levels"
    
    print("\n✅ TEST 4 PASSED: Adaptive hint levels working")


async def test_database_logging():
    """Test 5: Database logging"""
    print("\n" + "="*60)
    print("TEST 5: Database Logging")
    print("="*60)
    
    user = await sync_to_async(User.objects.get)(username='test_student')
    problem = await sync_to_async(CodingProblem.objects.first)()
    
    initial_count = await sync_to_async(CodeSubmission.objects.filter(user=user, problem=problem).count)()
    
    engine = SocraticCoderEngine()
    await engine.analyze_code_submission(
        user_id=user.id,
        problem_id=problem.id,
        code="def test(): pass",
        time_spent=45,
        emotion_valence=0.0
    )
    
    final_count = await sync_to_async(CodeSubmission.objects.filter(user=user, problem=problem).count)()
    
    print(f"✓ Initial submissions: {initial_count}")
    print(f"✓ Final submissions: {final_count}")
    print(f"✓ New submission created: {final_count > initial_count}")
    
    # Check latest submission
    latest = await sync_to_async(CodeSubmission.objects.filter(user=user, problem=problem).latest)('submitted_at')
    print(f"✓ Latest submission error type: {latest.error_type}")
    print(f"✓ Latest submission hint level: {latest.hint_level}")
    
    assert final_count > initial_count, "Should create new submission"
    print("\n✅ TEST 5 PASSED: Database logging working correctly")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print(" "*20 + "GAP 3 IMPLEMENTATION TEST SUITE")
    print("🚀"*30)
    
    try:
        await test_syntax_error()
        await test_logic_error()
        await test_struggle_detection()
        await test_hint_levels()
        await test_database_logging()
        
        print("\n" + "🎉"*30)
        print(" "*20 + "ALL TESTS PASSED!")
        print("🎉"*30)
        print("\n✅ Phase 1 (Gap 3) Implementation: COMPLETE")
        print("✅ Database Models: Working")
        print("✅ SocraticCoderEngine: Functional")
        print("✅ 5-Level Hint System: Operational")
        print("✅ Struggle Detection: Active")
        print("✅ Adaptive Personalization: Working")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

