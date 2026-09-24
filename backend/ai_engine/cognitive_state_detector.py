"""
Cognitive State Detector
Classifies WHY the student is struggling, not just WHEN.

This gives the Socratic mode engine the information it needs to choose
the most appropriate teaching hint for the teacher agent.

States
------
solved           → student reached correct solution
reasoning        → code is partially structured; student is thinking correctly
syntax_confusion → code fails to parse; student knows the idea but syntax is off
misconception    → code parses but logic is demonstrably wrong (pattern match)
guessing         → multiple random attempts or explicit guessing language in speech
stuck            → no code change for a long time; blank canvas

Rule-based first version — no LLM needed. Can be upgraded later.
"""

import ast
import re
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Speech phrases that signal guessing behaviour
_GUESSING_PHRASES = [
    "just try", "maybe", "i don't know", "i dont know",
    "random", "not sure", "guessing", "let me try",
    "i'll just", "ill just", "no idea", "what if i",
]

# Minimum attempt count before flagging guessing from speech alone
_GUESSING_MIN_ATTEMPTS = 2

# Seconds of inactivity that indicates a student is stuck
_STUCK_THRESHOLD_SECONDS = 30


@dataclass
class StruggleState:
    """Output of CognitiveStateDetector.detect()"""
    type: str        # reasoning | syntax_confusion | misconception | guessing | stuck | solved
    confidence: float  # 0.0–1.0
    evidence: str      # human-readable reason (used in hints and logging)


class CognitiveStateDetector:
    """
    Classifies a student's current cognitive struggle state.

    Usage
    -----
    detector = CognitiveStateDetector()
    state = detector.detect(
        canvas_state={"text_blocks": [...], "drawings": [...], "notes": [...]},
        code="for i in range(10)",
        attempt_count=2,
        speech_transcript="maybe I should just try this",
        time_since_last_action=20.0,
        is_solved=False,
    )
    # state.type == "syntax_confusion"
    """

    def detect(
        self,
        canvas_state: Optional[Dict[str, Any]],
        code: Optional[str],
        attempt_count: int,
        speech_transcript: Optional[str],
        time_since_last_action: float,
        is_solved: bool,
    ) -> StruggleState:
        """
        Evaluate signals and return a StruggleState.
        Rules are evaluated top-down; first match wins.
        """

        # ── Rule 1: Already solved ──────────────────────────────────────────
        if is_solved:
            return StruggleState(
                type="solved",
                confidence=1.0,
                evidence="PBL session marked as correct.",
            )

        # ── Rule 2: Blank / no code yet ─────────────────────────────────────
        normalised_code = (code or "").strip()
        canvas_has_content = self._canvas_has_content(canvas_state)

        if not normalised_code and not canvas_has_content and attempt_count == 0:
            # Student hasn't started — treat as listener territory, not stuck
            return StruggleState(
                type="reasoning",
                confidence=0.70,
                evidence="No code or canvas content yet. Student is getting started.",
            )

        # ── Rule 3: Syntax error ─────────────────────────────────────────────
        if normalised_code:
            syntax_issue = self._check_syntax(normalised_code)
            if syntax_issue:
                return StruggleState(
                    type="syntax_confusion",
                    confidence=0.95,
                    evidence=syntax_issue,
                )

        # ── Rule 4: Logic error (code parses but pattern is wrong) ───────────
        if normalised_code:
            logic_issue = self._check_logic_errors(normalised_code)
            if logic_issue:
                return StruggleState(
                    type="misconception",
                    confidence=0.80,
                    evidence=logic_issue,
                )

        # ── Rule 5: Guessing — speech signals ────────────────────────────────
        if speech_transcript and attempt_count >= _GUESSING_MIN_ATTEMPTS:
            transcript_lower = speech_transcript.lower()
            for phrase in _GUESSING_PHRASES:
                if phrase in transcript_lower:
                    return StruggleState(
                        type="guessing",
                        confidence=0.78,
                        evidence=f"Speech contained guessing phrase: '{phrase}'.",
                    )

        # ── Rule 6: Guessing — repeated attempts with no consistent direction ─
        # Signalled by attempt_count alone when code is still empty/unchanged
        if attempt_count >= 3 and not normalised_code:
            return StruggleState(
                type="guessing",
                confidence=0.72,
                evidence=f"{attempt_count} attempts but no code written. Likely guessing.",
            )

        # ── Rule 7: Stuck — long inactivity ──────────────────────────────────
        if time_since_last_action >= _STUCK_THRESHOLD_SECONDS:
            return StruggleState(
                type="stuck",
                confidence=0.85,
                evidence=f"No action for {time_since_last_action:.0f}s.",
            )

        # ── Rule 8: Code is valid and partially structured → reasoning ────────
        if normalised_code:
            return StruggleState(
                type="reasoning",
                confidence=0.75,
                evidence="Code is syntactically valid with no obvious logic errors. Student is thinking.",
            )

        # ── Default: stuck ────────────────────────────────────────────────────
        return StruggleState(
            type="stuck",
            confidence=0.60,
            evidence="No strong signal detected; defaulting to stuck.",
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _canvas_has_content(self, canvas_state: Optional[Dict[str, Any]]) -> bool:
        """Return True if the canvas JSON has any non-empty content."""
        if not canvas_state:
            return False
        text_blocks = canvas_state.get("text_blocks") or []
        drawings    = canvas_state.get("drawings") or []
        notes       = canvas_state.get("notes") or []
        return bool(text_blocks or drawings or notes)

    def _check_syntax(self, code: str) -> Optional[str]:
        """
        Try to parse code with Python's AST.
        Returns a human-readable error string if parsing fails, else None.
        Replicates SocraticCoderEngine._check_syntax() without the DB dependency.
        """
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            # IndentationError is a subclass of SyntaxError — caught here too
            label = "IndentationError" if isinstance(e, IndentationError) else "SyntaxError"
            return f"{label} on line {e.lineno}: {e.msg}"
        except Exception as e:
            return f"Parse error: {str(e)}"

    def _check_logic_errors(self, code: str) -> Optional[str]:
        """
        Pattern-based logic error detection.
        Returns a human-readable description if a pattern fires, else None.
        Mirrors SocraticCoderEngine._check_logic_errors() without DB dependency.
        """
        # Off-by-one: range(len(arr)) without -1
        if re.search(r'range\(len\([^)]+\)\)(?!.*-\s*1)', code):
            return "Potential off-by-one: range(len(arr)) may cause IndexError."

        # Infinite loop: while True without break
        if re.search(r'while\s+True:', code) and 'break' not in code:
            return "Infinite loop: while True with no break statement."

        # Loop variable never updated inside while loop
        while_match = re.search(r'while\s+(\w+)\s*[<>!=]=?\s', code)
        if while_match:
            loop_var = while_match.group(1)
            # A very simple heuristic: if loop_var doesn't appear after 'while' line
            loop_body = code[while_match.end():]
            if not re.search(rf'\b{re.escape(loop_var)}\s*[+\-*/]?=', loop_body):
                return f"Loop variable '{loop_var}' may never change, causing infinite loop."

        return None


# Module-level singleton
_detector: Optional[CognitiveStateDetector] = None


def get_cognitive_detector() -> CognitiveStateDetector:
    global _detector
    if _detector is None:
        _detector = CognitiveStateDetector()
    return _detector
