"""
adaptive_engine.py — Adjusts difficulty and picks next concept based on performance

Tracks:
  - mastery_score accumulation (0.0 – 1.0)
  - consecutive correct / incorrect streaks
  - hint usage penalty
  - attempt count scaling

Provides:
  update_mastery(session, attempt) → updated mastery_score + decision dict
  compute_new_difficulty(session)  → int 1–5
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ── Tuning constants ──────────────────────────────────────────────────────────

MASTERY_CORRECT_BASE     = 0.25   # base gain for a correct first attempt
MASTERY_CORRECT_HINT_PEN = 0.05   # per hint used
MASTERY_INCORRECT        = -0.08  # penalty per wrong attempt
MASTERY_MIN              = 0.0
MASTERY_MAX              = 1.0

MASTERY_THRESHOLD_UP   = 0.75    # above this → increase difficulty
MASTERY_THRESHOLD_DOWN = 0.30    # below this → decrease difficulty

STREAK_UP   = 2    # consecutive corrects before bumping difficulty
STREAK_DOWN = 3    # consecutive incorrects before dropping difficulty


# ── Main entry point ──────────────────────────────────────────────────────────

def update_mastery(session, attempt) -> Dict[str, Any]:
    """
    Called after each PBLAttempt is evaluated.

    Returns a dict:
    {
        "mastery_score":  float,
        "new_difficulty": int,
        "message":        str | None,   # optional toast message for student
        "session_end":    bool,          # True if mastery reached 1.0
    }
    """
    is_correct  = attempt.is_correct or False
    hint_count  = session.hint_count
    attempt_num = session.attempt_count

    # ── Delta calculation ────────────────────────────────────────────────
    if is_correct:
        delta  = MASTERY_CORRECT_BASE
        delta -= hint_count * MASTERY_CORRECT_HINT_PEN
        delta  = max(delta, 0.05)   # always give at least a small gain
    else:
        delta = MASTERY_INCORRECT * min(attempt_num, 3)  # cap penalty

    new_mastery = _clamp(session.mastery_score + delta)

    # ── Count streaks ────────────────────────────────────────────────────
    recent = list(
        session.attempts.order_by('-attempt_number')[:STREAK_UP + STREAK_DOWN]
    )
    recent_correct   = [a.is_correct for a in recent if a.is_correct is not None]
    consecutive_up   = _consecutive_tail(recent_correct, True,  STREAK_UP)
    consecutive_down = _consecutive_tail(recent_correct, False, STREAK_DOWN)

    # ── New difficulty ───────────────────────────────────────────────────
    current_d   = session.difficulty_level
    new_d       = current_d

    if new_mastery >= MASTERY_THRESHOLD_UP or consecutive_up >= STREAK_UP:
        new_d = min(current_d + 1, 5)
    elif new_mastery <= MASTERY_THRESHOLD_DOWN or consecutive_down >= STREAK_DOWN:
        new_d = max(current_d - 1, 1)

    # ── Update session (caller saves) ────────────────────────────────────
    session.mastery_score    = new_mastery
    session.difficulty_level = new_d

    # ── Build response ───────────────────────────────────────────────────
    session_end = new_mastery >= MASTERY_MAX
    message     = None

    if session_end:
        message = "Excellent! You've mastered this concept! Moving on…"
    elif new_d > current_d:
        message = "Great work! Raising the difficulty…"
    elif new_d < current_d:
        message = "Let's try an easier version to build confidence."

    result = {
        "mastery_score":  new_mastery,
        "new_difficulty": new_d,
        "message":        message,
        "session_end":    session_end,
    }

    logger.info(
        '[Adaptive] mastery %.2f→%.2f, difficulty %d→%d, session_end=%s',
        session.mastery_score, new_mastery, current_d, new_d, session_end,
    )
    return result


def compute_new_difficulty(session) -> int:
    """
    Lightweight read-only helper: what difficulty would we assign right now?
    """
    if session.mastery_score >= MASTERY_THRESHOLD_UP:
        return min(session.difficulty_level + 1, 5)
    if session.mastery_score <= MASTERY_THRESHOLD_DOWN:
        return max(session.difficulty_level - 1, 1)
    return session.difficulty_level


# ── Utilities ─────────────────────────────────────────────────────────────────

def _clamp(val: float) -> float:
    return max(MASTERY_MIN, min(MASTERY_MAX, val))


def _consecutive_tail(booleans, target: bool, max_n: int) -> int:
    """Count how many of the last (up to max_n) values equal `target`."""
    count = 0
    for v in reversed(booleans[:max_n]):
        if v == target:
            count += 1
        else:
            break
    return count
