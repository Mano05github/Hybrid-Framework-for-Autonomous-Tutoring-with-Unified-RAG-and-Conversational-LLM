"""
AnalystAgent — SIP Mastery Updater (v2 spec)

Responsibilities:
  1. Load the student's StudentIntelligenceProfile (SIP) from DB.
  2. Update mastery scores via Elo algorithm (with forgetting curve decay).
  3. Update confidence_index, streak, and consecutive_wrong counter.
  4. Recalculate revision_priority_queue from all topics.
  5. Persist changes back to DB.

This agent is called as a post-session hook — NOT through the live LangGraph
graph (which handles real-time turns). The graph's SessionOrchestrator calls
analyst_agent() after a mini-test completes.
"""
import logging
from typing import Optional, List

from .state import AgentState

logger = logging.getLogger(__name__)


def analyst_agent(state: AgentState) -> AgentState:
    """
    Post-session mastery update agent.

    Reads from state:
      - user_id           (str)
      - current_topic     (str — topic title or pk str)
      - quiz_data         (list of answered question dicts, each with 'correct' bool and 'points')
      - consecutive_wrong_answers (optional, kept in state for in-session use)

    Writes to state:
      - mastery_state     (topic → normalised 0–100 score)
    """
    from django.core.exceptions import ObjectDoesNotExist

    user_id    = state.get("user_id", "")
    topic_str  = state.get("current_topic", "")
    quiz_data  = state.get("quiz_data") or []

    if not user_id:
        logger.warning("[Analyst] No user_id in state — skipping mastery update")
        return state

    try:
        from core.models import StudentIntelligenceProfile, Topic

        # ── Load or create SIP ────────────────────────────────────────────────
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=int(user_id))
        sip, _created = StudentIntelligenceProfile.objects.get_or_create(user=user)

        # ── Resolve topic ID ──────────────────────────────────────────────────
        topic_id: Optional[int] = None
        try:
            topic_id = int(topic_str)
        except (ValueError, TypeError):
            # topic_str is a title — try to look it up
            topic_obj = Topic.objects.filter(title__iexact=topic_str).first()
            if topic_obj:
                topic_id = topic_obj.pk

        # ── Process quiz answers ───────────────────────────────────────────────
        total_points_earned = 0
        total_points_possible = 0

        for q in quiz_data:
            correct = bool(q.get("correct", False))
            points  = int(q.get("points", 0))
            total_points_possible += points
            if correct:
                total_points_earned += points
            if topic_id is not None:
                sip.update_mastery(topic_id=topic_id, correct=correct)

        # ── Update confidence_index ────────────────────────────────────────────
        if total_points_possible > 0:
            raw_pct = (total_points_earned / total_points_possible) * 100
            # EMA-style smoothing (70% existing + 30% new result)
            sip.confidence_index = sip.confidence_index * 0.7 + raw_pct * 0.3
            sip.confidence_index = max(0.0, min(100.0, sip.confidence_index))

        # ── Update daily streak ────────────────────────────────────────────────
        sip.update_streaks()

        # ── Recalculate revision priority queue ────────────────────────────────
        all_topic_ids = list(Topic.objects.values_list('pk', flat=True))
        sip.recalculate_revision_queue(all_topic_ids)

        # ── Persist ───────────────────────────────────────────────────────────
        sip.save()

        logger.info(
            f"[Analyst] SIP updated for user={user_id} | topic={topic_id} | "
            f"confidence={sip.confidence_index:.1f} | streak={sip.daily_streak}"
        )

        # ── Return mastery snapshot in state ──────────────────────────────────
        mastery_snapshot = {
            str(tid): sip.get_mastery_score(tid)
            for tid in sip.mastery_map
        }
        state["mastery_state"] = mastery_snapshot
        state["consecutive_wrong_answers"] = sip.consecutive_wrong_answers

    except Exception as e:
        logger.error(f"[Analyst] Error updating SIP: {e}", exc_info=True)

    return state


class AnalystAgent:
    """
    Class wrapper kept for backward compatibility.
    Delegates to the module-level analyst_agent() function.
    """

    def invoke(self, state: AgentState) -> dict:
        updated = analyst_agent(state)
        return {"user_mastery": updated.get("mastery_state", {})}

