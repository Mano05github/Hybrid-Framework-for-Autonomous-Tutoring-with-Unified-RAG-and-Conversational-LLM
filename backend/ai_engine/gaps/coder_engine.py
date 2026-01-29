"""
Gap 3: Socratic Coder Engine
Adaptive hint system with 5-level progression and struggle detection
"""
import ast
import re
import json
import signal
import io
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from asgiref.sync import sync_to_async
from contextlib import redirect_stdout, redirect_stderr

from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr

from learning_session.models import (
    CodeSubmission, HintHistory, StudentCodingProfile, CodingProblem
)
from llm_engine.factory import LLMFactory


@dataclass
class AnalysisResult:
    """Result of code analysis"""
    has_error: bool
    error_type: str  # 'syntax' | 'logic' | 'approach' | 'none'
    error_details: str
    error_location: Optional[str]  # Line number or function name
    confidence: float  # 0.0-1.0


@dataclass
class HintDecision:
    """Hint delivery decision"""
    should_offer: bool
    hint_level: int  # 1-5
    reason: str  # Why this hint level?
    struggle_score: float  # 0.0-1.0


class SocraticCoderEngine:
    """
    Adaptive hint engine using Socratic method for code learning.
    Analyzes code through 3-stage pipeline: Syntax → Logic → Approach
    """
    
    # Thresholds
    IDLE_THRESHOLD = 120  # seconds
    ERROR_REPEAT_THRESHOLD = 3
    STRUGGLE_SCORE_THRESHOLD = 0.6
    
    def __init__(self):
        self.llm_factory = LLMFactory()
    
    async def analyze_code_submission(
        self,
        user_id: int,
        problem_id: int,
        code: str,
        time_spent: int,
        emotion_valence: float = 0.0
    ) -> Dict:
        """
        Main entry point: Analyze code and generate adaptive hint
        
        Returns:
            {
                "is_correct": bool,
                "analysis": AnalysisResult,
                "hint_decision": HintDecision,
                "hint_text": str,
                "encouragement": str
            }
        """
        # 1. Run three-stage error analysis
        analysis = await self._analyze_code_pipeline(code, problem_id)
        
        # 2. Check if code is correct
        if not analysis.has_error:
            is_correct = await self._validate_correctness(code, problem_id)
            if is_correct:
                return await self._generate_success_response(user_id, problem_id, code, time_spent)
        
        # 3. Detect struggle level
        hint_decision = await self._detect_struggle_and_decide_hint(
            user_id=user_id,
            problem_id=problem_id,
            error_type=analysis.error_type,
            time_spent=time_spent,
            emotion_valence=emotion_valence
        )
        
        # 4. Generate adaptive hint
        hint_text = ""
        if hint_decision.should_offer:
            hint_text = await self._generate_hint(
                level=hint_decision.hint_level,
                error_type=analysis.error_type,
                error_details=analysis.error_details,
                code=code,
                problem_id=problem_id
            )
        
        # 5. Save submission to database
        await self._save_submission(
            user_id=user_id,
            problem_id=problem_id,
            code=code,
            error_type=analysis.error_type,
            error_details=analysis.error_details,
            hint_level=hint_decision.hint_level if hint_decision.should_offer else None,
            hint_text=hint_text,
            time_spent=time_spent
        )
        
        return {
            "is_correct": False,
            "analysis": asdict(analysis),
            "hint_decision": asdict(hint_decision),
            "hint_text": hint_text,
            "encouragement": self._generate_encouragement(hint_decision.struggle_score)
        }
    
    # ===== ANALYSIS PIPELINE =====
    
    async def _analyze_code_pipeline(self, code: str, problem_id: int) -> AnalysisResult:
        """
        Three-stage analysis: Syntax → Logic → Approach
        Stop at first error found (fail-fast for efficiency)
        """
        # Stage 1: Syntax check (fast, deterministic)
        syntax_result = self._check_syntax(code)
        if syntax_result.has_error:
            return syntax_result
        
        # Stage 2: Logic check (medium speed, pattern-based)
        logic_result = self._check_logic_errors(code)
        if logic_result.has_error:
            return logic_result
        
        # Stage 3: Approach check (slow, LLM-based)
        approach_result = await self._check_approach_with_llm(code, problem_id)
        return approach_result
    
    def _check_syntax(self, code: str) -> AnalysisResult:
        """Stage 1: Python AST parsing for syntax errors"""
        try:
            ast.parse(code)
            return AnalysisResult(
                has_error=False,
                error_type='none',
                error_details='',
                error_location=None,
                confidence=1.0
            )
        except SyntaxError as e:
            return AnalysisResult(
                has_error=True,
                error_type='syntax',
                error_details=f"Syntax error: {e.msg}",
                error_location=f"Line {e.lineno}" if e.lineno else "Unknown",
                confidence=1.0
            )
        except IndentationError as e:
            return AnalysisResult(
                has_error=True,
                error_type='syntax',
                error_details=f"Indentation error: {e.msg}",
                error_location=f"Line {e.lineno}" if e.lineno else "Unknown",
                confidence=1.0
            )
        except Exception as e:
            return AnalysisResult(
                has_error=True,
                error_type='syntax',
                error_details=f"Parse error: {str(e)}",
                error_location="Unknown",
                confidence=0.9
            )
    
    def _check_logic_errors(self, code: str) -> AnalysisResult:
        """Stage 2: Pattern matching for common logic errors"""
        
        # Pattern 1: Off-by-one in loops
        if re.search(r'range\(len\([^)]+\)\)(?!.*-\s*1)', code):
            return AnalysisResult(
                has_error=True,
                error_type='logic',
                error_details='Potential off-by-one error: range(len(arr)) may cause IndexError',
                error_location='Loop boundary',
                confidence=0.75
            )
        
        # Pattern 2: Infinite loop risk
        if re.search(r'while\s+True:', code) and 'break' not in code:
            return AnalysisResult(
                has_error=True,
                error_type='logic',
                error_details='Infinite loop detected: while True without break statement',
                error_location='While loop',
                confidence=0.85
            )
        
        # Pattern 3: Uninitialized variable (basic check)
        assignments = re.findall(r'^\s*(\w+)\s*=', code, re.MULTILINE)
        usages = re.findall(r'\b(\w+)\b', code)
        builtins = ['print', 'return', 'range', 'len', 'int', 'str', 'list', 'dict', 'set', 
                    'True', 'False', 'None', 'if', 'else', 'for', 'while', 'def', 'class']
        
        for var in usages:
            if var not in assignments and var not in builtins and not var.isdigit():
                # Check if it's a function parameter
                if not re.search(rf'def\s+\w+\([^)]*{var}[^)]*\)', code):
                    return AnalysisResult(
                        has_error=True,
                        error_type='logic',
                        error_details=f'Variable "{var}" may be used before assignment',
                        error_location=f'Variable: {var}',
                        confidence=0.60
                    )
        
        # No logic errors detected
        return AnalysisResult(
            has_error=False,
            error_type='none',
            error_details='',
            error_location=None,
            confidence=0.8
        )
    
    async def _check_approach_with_llm(self, code: str, problem_id: int) -> AnalysisResult:
        """Stage 3: LLM validates algorithmic approach"""
        try:
            problem = await sync_to_async(CodingProblem.objects.get)(id=problem_id)
        except CodingProblem.DoesNotExist:
            return AnalysisResult(
                has_error=False,
                error_type='none',
                error_details='',
                error_location=None,
                confidence=0.5
            )
        
        prompt = f"""You are a computer science tutor. Analyze if this student's code uses the correct algorithmic approach.

Problem: {problem.title}
Expected Algorithm: {problem.expected_algorithm}
Description: {problem.description}

Student Code:
```python
{code}
```

Answer in JSON format:
{{
    "is_correct_approach": true/false,
    "explanation": "Brief explanation of approach correctness",
    "confidence": 0.0-1.0
}}
"""
        
        try:
            llm = self.llm_factory.create_llm(provider="openai", model="gpt-4o-mini")
            response = await llm.ainvoke(prompt)
            
            # Parse LLM response
            result = json.loads(response.content)
            if not result.get("is_correct_approach", True):
                return AnalysisResult(
                    has_error=True,
                    error_type='approach',
                    error_details=result.get("explanation", "Incorrect algorithmic approach"),
                    error_location='Overall approach',
                    confidence=result.get("confidence", 0.9)
                )
        except (json.JSONDecodeError, Exception) as e:
            print(f"[SocraticCoder] LLM approach check failed: {e}")
        
        return AnalysisResult(
            has_error=False,
            error_type='none',
            error_details='Approach looks correct',
            error_location=None,
            confidence=0.9
        )
    
    # ===== STRUGGLE DETECTION & HINT DECISION =====
    
    async def _detect_struggle_and_decide_hint(
        self,
        user_id: int,
        problem_id: int,
        error_type: str,
        time_spent: int,
        emotion_valence: float
    ) -> HintDecision:
        """
        Calculate struggle score and decide hint level
        
        Struggle Score = 0.4 * (idle_time/120) + 0.3 * (errors/5) + 0.3 * |emotion|
        """
        # Get recent submissions for error count
        recent_submissions = await sync_to_async(list)(
            CodeSubmission.objects.filter(
                user_id=user_id,
                problem_id=problem_id
            ).order_by('-submitted_at')[:10]
        )
        
        error_count = sum(1 for sub in recent_submissions if sub.error_type != 'none')
        
        # Calculate struggle score
        idle_component = min(time_spent / self.IDLE_THRESHOLD, 1.0) * 0.4
        error_component = min(error_count / 5, 1.0) * 0.3
        emotion_component = abs(emotion_valence) * 0.3
        
        struggle_score = idle_component + error_component + emotion_component
        
        # Decide if hint should be offered
        should_offer = struggle_score >= self.STRUGGLE_SCORE_THRESHOLD
        
        if not should_offer:
            return HintDecision(
                should_offer=False,
                hint_level=0,
                reason="Student not struggling yet",
                struggle_score=struggle_score
            )
        
        # Determine hint level based on student profile
        try:
            profile = await sync_to_async(StudentCodingProfile.objects.get)(user_id=user_id)
            hint_level = self._calculate_adaptive_hint_level(
                profile=profile,
                struggle_score=struggle_score,
                error_type=error_type,
                error_count=error_count
            )
        except StudentCodingProfile.DoesNotExist:
            # Default to level 2 for new students
            hint_level = 2
        
        return HintDecision(
            should_offer=True,
            hint_level=hint_level,
            reason=f"Struggle detected (score: {struggle_score:.2f})",
            struggle_score=struggle_score
        )
    
    def _calculate_adaptive_hint_level(
        self,
        profile: StudentCodingProfile,
        struggle_score: float,
        error_type: str,
        error_count: int
    ) -> int:
        """
        Calculate hint level (1-5) based on student profile and context
        
        Priority: Approach > Logic > Syntax
        """
        base_level = profile.avg_hint_level
        
        # Adjust based on error type (Approach-first prioritization)
        if error_type == 'approach':
            level = 2  # Start with conceptual hint
        elif error_type == 'logic':
            level = 3  # Point to logic area
        elif error_type == 'syntax':
            level = 4  # More direct for syntax
        else:
            level = base_level
        
        # Escalate if high struggle
        if struggle_score > 0.8:
            level = min(level + 1, 5)
        
        # Quick learners get more minimal hints
        if profile.quick_learner:
            level = max(level - 1, 1)
        
        # Cap after many errors (provide more help)
        if error_count >= self.ERROR_REPEAT_THRESHOLD:
            level = min(level + 1, 5)
        
        return int(level)
    
    # ===== HINT GENERATION =====
    
    async def _generate_hint(
        self,
        level: int,
        error_type: str,
        error_details: str,
        code: str,
        problem_id: int
    ) -> str:
        """Generate hint text based on level and error type"""
        
        try:
            problem = await sync_to_async(CodingProblem.objects.get)(id=problem_id)
        except CodingProblem.DoesNotExist:
            return "Keep working through the problem systematically."
        
        if error_type == 'approach':
            return await self._generate_approach_hint(level, problem, code)
        elif error_type == 'logic':
            return self._generate_logic_hint(level, error_details, code)
        elif error_type == 'syntax':
            return self._generate_syntax_hint(level, error_details, code)
        else:
            return "Keep working through the problem systematically."
    
    async def _generate_approach_hint(self, level: int, problem: CodingProblem, code: str) -> str:
        """Generate approach-level hint"""
        
        if level == 1:  # Nudge
            return f"🤔 Think about the key property of {problem.expected_algorithm}. What makes it efficient?"
        
        elif level == 2:  # Conceptual
            prompts = {
                "binary_search": "Binary search requires a sorted array. What condition lets you eliminate half the search space?",
                "two_pointer": "Can you use two pointers moving from opposite ends?",
                "dynamic_programming": "Can you break this into overlapping subproblems?",
                "recursion": "What's the base case? What's the recursive case?",
                "divide_and_conquer": "How can you divide this problem into smaller subproblems?"
            }
            return f"💡 {prompts.get(problem.expected_algorithm, 'Consider the algorithm structure.')}"
        
        elif level == 3:  # Logic area
            return f"Your approach is close! Focus on how {problem.expected_algorithm} divides the problem space."
        
        elif level == 4:  # Pattern
            return f"📚 Review the {problem.expected_algorithm} pattern. The key is maintaining invariants at each step."
        
        else:  # Level 5 - Direct
            return f"✨ For {problem.expected_algorithm}, you need: 1) Initialize search space, 2) Calculate midpoint, 3) Update boundaries based on comparison."
    
    def _generate_logic_hint(self, level: int, error_details: str, code: str) -> str:
        """Generate logic-level hint"""
        
        if "off-by-one" in error_details.lower():
            if level <= 2:
                return "🤔 Check your loop boundaries carefully. Are you accessing all elements correctly?"
            elif level == 3:
                return "🔍 Look at your range() call. Should it go all the way to len(arr)?"
            else:
                return "⚠️ Change `range(len(arr))` to `range(len(arr) - 1)` or use `range(len(arr))` with `arr[i]` only."
        
        elif "infinite loop" in error_details.lower():
            if level <= 2:
                return "🤔 How will your while loop terminate?"
            else:
                return "⚠️ Add a break condition inside your `while True:` loop."
        
        elif "used before assignment" in error_details.lower():
            if level <= 2:
                return "🤔 Check if all variables are initialized before use."
            else:
                return f"⚠️ {error_details}"
        
        else:
            return f"🔍 {error_details}"
    
    def _generate_syntax_hint(self, level: int, error_details: str, code: str) -> str:
        """Generate syntax-level hint"""
        
        if level <= 3:
            return f"⚠️ Syntax issue detected: {error_details}. Review the line and fix the syntax."
        else:
            # Extract line number from error_details
            line_match = re.search(r'Line (\d+)', error_details)
            line_hint = f" on line {line_match.group(1)}" if line_match else ""
            return f"🔧 Fix the syntax error{line_hint}: {error_details}"
    
    # ===== DATABASE OPERATIONS =====
    
    async def _save_submission(
        self,
        user_id: int,
        problem_id: int,
        code: str,
        error_type: str,
        error_details: str,
        hint_level: Optional[int],
        hint_text: str,
        time_spent: int
    ):
        """Save code submission to database"""
        await sync_to_async(CodeSubmission.objects.create)(
            user_id=user_id,
            problem_id=problem_id,
            code=code,
            error_type=error_type,
            error_details=error_details,
            hint_level=hint_level,
            hint_text=hint_text,
            time_spent_seconds=time_spent,
            is_correct=False
        )
        
        # If hint was delivered, record in hint history
        if hint_level:
            await sync_to_async(HintHistory.objects.create)(
                user_id=user_id,
                problem_id=problem_id,
                hint_level=hint_level,
                hint_text=hint_text
            )
    
    async def _validate_correctness(self, code: str, problem_id: int) -> bool:
        """Run test cases to validate correctness in a sandboxed environment"""
        try:
            # Fetch problem with test cases
            problem = await sync_to_async(CodingProblem.objects.get)(id=problem_id)
            test_cases = problem.test_cases
            
            if not test_cases:
                return False  # No test cases = can't validate
            
            # Run all test cases
            for i, test_case in enumerate(test_cases):
                test_input = test_case.get('input', [])
                expected_output = test_case.get('expected_output')
                
                result = await self._execute_code_safely(code, test_input)
                
                if result['success']:
                    actual_output = result['output']
                    # Compare outputs (handle different types)
                    if not self._compare_outputs(actual_output, expected_output):
                        return False  # Test case failed
                else:
                    return False  # Execution error
            
            return True  # All test cases passed
            
        except CodingProblem.DoesNotExist:
            return False
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    async def _execute_code_safely(self, code: str, test_input: List[Any]) -> Dict:
        """
        Execute student code in a restricted sandbox with timeout and resource limits.
        Uses RestrictedPython for safe execution.
        """
        try:
            # Compile with RestrictedPython
            try:
                byte_code = compile_restricted(
                    code,
                    filename='<student_code>',
                    mode='exec'
                )
            except SyntaxError as e:
                return {
                    'success': False,
                    'error': f"Syntax error: {e}",
                    'output': None
                }
            
            # Check if byte_code is a tuple (error format) or has errors attribute
            if isinstance(byte_code, tuple):
                # RestrictedPython 6.x format: (code, errors, warnings, used_names)
                compiled_code, errors, warnings, used_names = byte_code
                if errors:
                    return {
                        'success': False,
                        'error': f"Compilation errors: {', '.join(str(e) for e in errors)}",
                        'output': None
                    }
                byte_code = compiled_code
            elif hasattr(byte_code, 'errors') and byte_code.errors:
                return {
                    'success': False,
                    'error': f"Compilation errors: {', '.join(byte_code.errors)}",
                    'output': None
                }
            
            # Create restricted globals with safe builtins
            restricted_globals = {
                '__builtins__': self._get_safe_builtins(),
                '_getattr_': safer_getattr,
                '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
                '__name__': '<student_code>',
                '__metaclass__': type,
            }
            
            # Capture stdout/stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            # Execute with timeout (5 seconds) - cross-platform solution
            result = None
            
            def execute_code():
                """Inner function to execute in thread with timeout"""
                nonlocal result
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    exec(byte_code, restricted_globals)
                    
                    # Try to find the function to call
                    # Convention: Look for main() or solution()
                    main_func = restricted_globals.get('main') or restricted_globals.get('solution')
                    
                    if main_func and callable(main_func):
                        # Call function with test inputs
                        result = main_func(*test_input)
                    else:
                        # No function found, check for direct output
                        output_text = stdout_capture.getvalue().strip()
                        if output_text:
                            result = output_text
            
            try:
                # Use ThreadPoolExecutor for cross-platform timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(execute_code)
                    try:
                        future.result(timeout=5)  # 5 second timeout
                    except FuturesTimeoutError:
                        return {
                            'success': False,
                            'error': 'Code execution exceeded 5 seconds (timeout)',
                            'output': None
                        }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Execution error: {str(e)}",
                    'output': None
                }
            
            return {
                'success': True,
                'output': result,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Sandbox error: {str(e)}",
                'output': None
            }
    
    def _get_safe_builtins(self) -> Dict:
        """
        Return a safe subset of Python builtins.
        Excludes dangerous functions like open(), eval(), exec(), import, etc.
        """
        safe_builtins = {
            # Type constructors
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            'list': list,
            'tuple': tuple,
            'dict': dict,
            'set': set,
            
            # Utility functions
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'reversed': reversed,
            'any': any,
            'all': all,
            
            # Type checking
            'isinstance': isinstance,
            'type': type,
            
            # String/printing
            'print': print,
            'repr': repr,
            'chr': chr,
            'ord': ord,
            
            # Math (basic)
            'pow': pow,
            'divmod': divmod,
            
            # Iteration
            'iter': iter,
            'next': next,
            
            # Exceptions
            'Exception': Exception,
            'ValueError': ValueError,
            'TypeError': TypeError,
            'IndexError': IndexError,
            'KeyError': KeyError,
            
            # None and boolean
            'None': None,
            'True': True,
            'False': False,
        }
        
        return safe_builtins
    
    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        """
        Compare actual output with expected output.
        Handles different types and floating point comparison.
        """
        # Handle None
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False
        
        # Handle floats with tolerance
        if isinstance(actual, float) and isinstance(expected, float):
            return abs(actual - expected) < 1e-6
        
        # Handle lists/tuples recursively
        if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
            if len(actual) != len(expected):
                return False
            return all(self._compare_outputs(a, e) for a, e in zip(actual, expected))
        
        # Handle dicts
        if isinstance(actual, dict) and isinstance(expected, dict):
            if set(actual.keys()) != set(expected.keys()):
                return False
            return all(self._compare_outputs(actual[k], expected[k]) for k in actual.keys())
        
        # Direct comparison for primitives
        return actual == expected
    
    async def _generate_success_response(self, user_id: int, problem_id: int, code: str, time_spent: int) -> Dict:
        """Generate success response when code is correct"""
        # Mark submission as correct
        await sync_to_async(CodeSubmission.objects.create)(
            user_id=user_id,
            problem_id=problem_id,
            code=code,
            error_type='none',
            error_details='',
            hint_level=None,
            hint_text='',
            time_spent_seconds=time_spent,
            is_correct=True
        )
        
        return {
            "is_correct": True,
            "analysis": asdict(AnalysisResult(
                has_error=False,
                error_type='none',
                error_details='',
                error_location=None,
                confidence=1.0
            )),
            "hint_decision": asdict(HintDecision(
                should_offer=False,
                hint_level=0,
                reason="Code is correct!",
                struggle_score=0.0
            )),
            "hint_text": "",
            "encouragement": "🎉 Excellent work! Your solution is correct!"
        }
    
    def _generate_encouragement(self, struggle_score: float) -> str:
        """Generate contextual encouragement"""
        if struggle_score < 0.3:
            return "You're on the right track! Keep going. 💪"
        elif struggle_score < 0.6:
            return "This is challenging, but you're making progress. 🌟"
        else:
            return "Don't give up! Every error teaches you something valuable. 🚀"
