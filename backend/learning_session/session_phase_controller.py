"""
SessionPhaseController — v2 5-Phase Teaching Session Model

Phases (in order):
  1. diagnostic   – 1–2 probe questions to assess prior knowledge
  2. explanation  – structured teacher explanation (Khan Academy canvas mode)
  3. practice     – guided Q&A; track correctness
  4. adjustment   – adaptive difficulty engine triggered by consecutive errors
  5. minitest     – 5-question progressive MCQ; calls AnalystAgent on submit

The controller is session-scoped (stored in SessionOrchestrator.context).
It does NOT replace the LangGraph graph — it wraps it, deciding WHICH prompt
style / agent routing hint to inject based on the current phase.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# ── Phase constants ───────────────────────────────────────────────────────────
PHASE_DIAGNOSTIC   = "diagnostic"
PHASE_EXPLANATION  = "explanation"
PHASE_PRACTICE     = "practice"
PHASE_ADJUSTMENT   = "adjustment"
PHASE_MINITEST     = "minitest"

PHASE_ORDER = [
    PHASE_DIAGNOSTIC,
    PHASE_EXPLANATION,
    PHASE_PRACTICE,
    PHASE_ADJUSTMENT,
    PHASE_MINITEST,
]

# Minimum turns before advancing from diagnostic → explanation
DIAGNOSTIC_MIN_TURNS = 2

# Minimum correct answers in practice before moving to minitest
PRACTICE_CORRECT_TARGET = 3

# Trigger adjustment phase after this many consecutive wrong answers
CONSECUTIVE_WRONG_TRIGGER = 2


@dataclass
class PhaseState:
    """Lightweight in-memory phase tracking (not persisted to DB)."""
    current_phase: str       = PHASE_DIAGNOSTIC
    turns_in_phase: int      = 0
    correct_in_practice: int = 0
    wrong_in_practice: int   = 0
    consecutive_wrong: int   = 0
    reinforcement_active: bool = False
    reinforcement_failures: int = 0
    phase_history: List[str] = field(default_factory=list)

    def advance(self, to_phase: Optional[str] = None):
        """Move to next phase (or an explicit phase)."""
        self.phase_history.append(self.current_phase)
        if to_phase:
            self.current_phase = to_phase
        else:
            idx = PHASE_ORDER.index(self.current_phase)
            if idx < len(PHASE_ORDER) - 1:
                self.current_phase = PHASE_ORDER[idx + 1]
        self.turns_in_phase = 0
        logger.info(f"[Phase] → {self.current_phase}")


class SessionPhaseController:
    """
    Decides phase transitions and injects phase-specific hints into the
    LangGraph state before every turn.

    Usage in SessionOrchestrator.get_ai_response():
        phase_ctx = self.phase_controller.build_phase_context(user_message, sip)
        # merge phase_ctx into the LangGraph inputs dict
    """

    def __init__(self):
        self.phase_state = PhaseState()

    def current_phase(self) -> str:
        return self.phase_state.current_phase

    def build_phase_context(
        self,
        user_message: str,
        mastery_score: float = 70.0,
    ) -> Dict[str, Any]:
        """
        Returns a dict of extra fields to merge into LangGraph state.
        Called BEFORE invoking the graph.
        """
        ps = self.phase_state
        ps.turns_in_phase += 1

        ctx: Dict[str, Any] = {
            "session_phase": ps.current_phase,
        }

        # ── Phase-specific hints ─────────────────────────────────────────────
        if ps.current_phase == PHASE_DIAGNOSTIC:
            ctx["teaching_hint"] = (
                "You are in the DIAGNOSTIC phase. Ask 1–2 short questions to probe "
                "the student's prior knowledge on this topic. Do NOT explain yet — "
                "just gauge what they already know."
            )
            # Auto-advance after minimum diagnostic turns
            if ps.turns_in_phase >= DIAGNOSTIC_MIN_TURNS:
                ps.advance(PHASE_EXPLANATION)

        elif ps.current_phase == PHASE_EXPLANATION:
            ctx["teaching_hint"] = (
                "You are in the EXPLANATION phase. Give a full structured explanation "
                "using the Khan Academy canvas drawing style. End with one quick-check question."
            )
            # Move to practice after first explanation turn
            if ps.turns_in_phase >= 1:
                ps.advance(PHASE_PRACTICE)

        elif ps.current_phase == PHASE_PRACTICE:
            ctx["teaching_hint"] = (
                "You are in the GUIDED PRACTICE phase. Ask the student one practice question. "
                "If they answer correctly, praise them and give a slightly harder follow-up. "
                "If wrong, use the Socratic method: ask a guiding question instead of correcting directly."
            )
            # Check for minitest trigger
            if ps.correct_in_practice >= PRACTICE_CORRECT_TARGET:
                ps.advance(PHASE_MINITEST)
            elif ps.consecutive_wrong >= CONSECUTIVE_WRONG_TRIGGER:
                ps.advance(PHASE_ADJUSTMENT)

        elif ps.current_phase == PHASE_ADJUSTMENT:
            if not ps.reinforcement_active:
                ps.reinforcement_active = True
                ctx["teaching_hint"] = (
                    "You are in the CONCEPT REINFORCEMENT sub-mode. The student is struggling. "
                    "Give a SHORT, simplified re-explanation of the core concept "
                    "(2–3 sentences max), then ONE visual example, then ask ONE guided question."
                )
            elif ps.reinforcement_failures >= 3:
                # Break topic into sub-concept
                ctx["teaching_hint"] = (
                    "The student is still struggling after reinforcement. Break this topic down "
                    "into its smallest sub-concept. Explain ONLY that sub-concept this turn."
                )
            else:
                ctx["teaching_hint"] = (
                    "Continue guiding the student gently. If they answer correctly, "
                    "return to normal practice mode."
                )

        elif ps.current_phase == PHASE_MINITEST:
            ctx["teaching_hint"] = (
                "You are in the MINI TEST phase. Do not teach — generate or present "
                "a quiz question. Route to the examiner agent."
            )
            # Override intent so supervisor routes to examiner
            ctx["intent_override"] = "examiner"

        return ctx

    def record_answer(self, correct: bool):
        """
        Call this after an answer is evaluated (practice or minitest).
        Updates internal counters and triggers phase transitions as needed.
        """
        ps = self.phase_state

        if correct:
            ps.consecutive_wrong      = 0
            ps.reinforcement_failures = 0
            if ps.current_phase == PHASE_PRACTICE:
                ps.correct_in_practice += 1
            if ps.reinforcement_active and ps.current_phase == PHASE_ADJUSTMENT:
                # Recovered — return to practice
                ps.reinforcement_active = False
                ps.advance(PHASE_PRACTICE)
        else:
            ps.consecutive_wrong   += 1
            ps.wrong_in_practice   += 1
            if ps.current_phase == PHASE_ADJUSTMENT and ps.reinforcement_active:
                ps.reinforcement_failures += 1

        # Check practice → adjustment transition
        if (ps.current_phase == PHASE_PRACTICE
                and ps.consecutive_wrong >= CONSECUTIVE_WRONG_TRIGGER):
            ps.advance(PHASE_ADJUSTMENT)

        # Check practice → minitest transition
        if (ps.current_phase == PHASE_PRACTICE
                and ps.correct_in_practice >= PRACTICE_CORRECT_TARGET):
            ps.advance(PHASE_MINITEST)

    def reset(self):
        """Start a fresh session (new topic)."""
        self.phase_state = PhaseState()
