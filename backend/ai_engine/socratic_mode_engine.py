"""
Socratic Mode Engine
Decides WHICH teaching mode to enter and generates the teaching_hint
that gets injected into the teacher agent's system prompt.

Modes
-----
listener      → Student is actively thinking; AI observes silently
nudge         → Student is slightly stuck; one focused guiding question
deep_guidance → Student is stuck after multiple attempts; step-by-step sub-questions
reflection    → Student just solved the problem; consolidate understanding

The engine combines:
  - PBL session signals  (attempt_count, hint_count, is_solved)
  - Timing signal        (time_since_last_action_seconds, from frontend)
  - Cognitive state      (StruggleState from CognitiveStateDetector)

Output: SocraticDecision(mode, teaching_hint)
The teaching_hint is injected verbatim into state["teaching_hint"], which
teacher_agent reads via its existing phase_section_s block.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .cognitive_state_detector import StruggleState

logger = logging.getLogger(__name__)

# Thresholds
_NUDGE_TIME_THRESHOLD      = 15   # seconds of inactivity before nudge
_DEEP_GUIDANCE_ATTEMPTS    = 3    # attempt count that triggers deep guidance
_DEEP_GUIDANCE_HINTS       = 3    # hint count that triggers deep guidance (alternative)

# Safety rule appended to every teaching hint
_SAFETY_RULE = (
    " IMPORTANT: Never reveal the final solution unless the student explicitly "
    "asks after multiple failed attempts."
)


@dataclass
class SocraticDecision:
    """Output of SocraticModeEngine.decide_mode()"""
    mode: str           # listener | nudge | deep_guidance | reflection
    teaching_hint: str  # injected into teacher_agent system prompt


# ── Hint templates per (mode, struggle_type) ────────────────────────────────
# Keys: (mode, struggle_type) — fall back to (mode, "default") if no specific match

_HINTS: Dict[Tuple[str, str], str] = {

    # ── LISTENER ──────────────────────────────────────────────────────────────
    ("listener", "default"): (
        "The student is actively working. Briefly acknowledge their thinking in one "
        "warm sentence. Do NOT ask a question yet — let them continue."
    ),

    # ── NUDGE ─────────────────────────────────────────────────────────────────
    ("nudge", "syntax_confusion"): (
        "The student has a Python syntax issue but understands the concept. Ask ONE "
        "targeted question about the specific syntax rule — NEVER name the fix. "
        "Example: 'What symbol typically ends a function or loop definition in Python?'"
    ),
    ("nudge", "misconception"): (
        "The student has a logic misconception. Ask ONE question about what they "
        "EXPECT their code to do, not what is wrong with it. "
        "E.g. 'Walk me through what happens to the variable on each iteration.'"
    ),
    ("nudge", "guessing"): (
        "The student appears to be guessing. Redirect calmly: ask what the "
        "problem is actually asking for BEFORE writing any code. "
        "E.g. 'What should the output look like when this runs?'"
    ),
    ("nudge", "stuck"): (
        "The student is stuck. Ask one small question that breaks the problem "
        "into its very first step. E.g. 'What is the simplest thing the loop needs to do?'"
    ),
    ("nudge", "reasoning"): (
        "The student is on the right track but paused. Acknowledge what they have "
        "so far, then ask ONE question to help them take the next logical step."
    ),
    ("nudge", "default"): (
        "The student needs a gentle nudge. Ask ONE focused guiding question. "
        "Do not give the answer."
    ),

    # ── DEEP GUIDANCE ─────────────────────────────────────────────────────────
    ("deep_guidance", "syntax_confusion"): (
        "The student is repeatedly struggling with syntax. Guide step-by-step: "
        "1) Ask what each line is supposed to do. "
        "2) Ask what they notice about the end of the loop/function line. "
        "3) If still stuck, ask 'What is the difference between a statement and a block defintion in Python?'"
    ),
    ("deep_guidance", "misconception"): (
        "The student has a persistent conceptual misunderstanding. Guide step-by-step: "
        "1) Ask what the variable should hold at the start. "
        "2) Ask whether it is changing on each iteration. "
        "3) Ask what happens when the loop finishes. "
        "Keep each question short and wait for their answer."
    ),
    ("deep_guidance", "guessing"): (
        "The student is making random attempts. STOP code-writing entirely. "
        "Ask them to describe the expected output in plain English first. "
        "Then walk through: 1) What repeats? 2) What changes each time? 3) When does it stop?"
    ),
    ("deep_guidance", "stuck"): (
        "The student is completely stuck after multiple attempts. Use the smallest "
        "possible steps: 1) What is the problem asking for in one sentence? "
        "2) What is the very first thing you need? "
        "3) How would you write just THAT one part?"
    ),
    ("deep_guidance", "reasoning"): (
        "The student is partially on track but needs structured support. "
        "Ask them to explain their current approach out loud step by step, "
        "then identify where the logic breaks."
    ),
    ("deep_guidance", "default"): (
        "The student is struggling after multiple attempts. Break the problem into "
        "small sub-questions. Ask one at a time and wait for each answer."
    ),

    # ── REFLECTION ────────────────────────────────────────────────────────────
    ("reflection", "solved"): (
        "The student just solved the problem. Celebrate briefly and warmly. Then ask "
        "ONE reflective question: why does this solution work? OR what would happen "
        "if the input were empty or very large? Help them generalise the insight."
    ),
    ("reflection", "default"): (
        "The student solved the problem. Congratulate them, then ask one question "
        "to consolidate the learning: 'Can you explain in your own words why this works?'"
    ),
}


def _get_hint(mode: str, struggle_type: str) -> str:
    """Look up teaching hint by mode + struggle_type, falling back to default."""
    key = (mode, struggle_type)
    hint = _HINTS.get(key) or _HINTS.get((mode, "default"), "Guide the student Socratically.")
    return hint + _SAFETY_RULE


class SocraticModeEngine:
    """
    Decides which Socratic mode to use and builds the teaching_hint.

    Usage
    -----
    engine = SocraticModeEngine()
    decision = engine.decide_mode(
        is_solved=False,
        attempt_count=2,
        hint_count=1,
        time_since_last_action=20.0,
        struggle_state=StruggleState(type="syntax_confusion", ...),
    )
    # decision.mode == "nudge"
    # decision.teaching_hint == "The student has a Python syntax issue..."
    """

    def decide_mode(
        self,
        is_solved: bool,
        attempt_count: int,
        hint_count: int,
        time_since_last_action: float,
        struggle_state: Optional[StruggleState],
    ) -> SocraticDecision:

        struggle_type = struggle_state.type if struggle_state else "default"

        # ── Decision tree ────────────────────────────────────────────────────
        if is_solved:
            mode = "reflection"

        elif attempt_count >= _DEEP_GUIDANCE_ATTEMPTS or hint_count >= _DEEP_GUIDANCE_HINTS:
            mode = "deep_guidance"

        elif time_since_last_action >= _NUDGE_TIME_THRESHOLD or attempt_count >= 1:
            mode = "nudge"

        else:
            mode = "listener"

        teaching_hint = _get_hint(mode, struggle_type)

        logger.info(
            "[SocraticModeEngine] mode=%s struggle=%s attempts=%d hints=%d idle=%.0fs solved=%s",
            mode, struggle_type, attempt_count, hint_count, time_since_last_action, is_solved,
        )

        return SocraticDecision(mode=mode, teaching_hint=teaching_hint)


# Module-level singleton
_engine: Optional[SocraticModeEngine] = None


def get_socratic_engine() -> SocraticModeEngine:
    global _engine
    if _engine is None:
        _engine = SocraticModeEngine()
    return _engine
