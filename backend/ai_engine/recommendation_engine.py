"""
RecommendationEngine — v2 post-session topic recommendation

Runs after every session (called by SessionOrchestrator.finalize_quiz).
Outputs:
  - top 3 recommended topics for the student
  - updated revision_priority_queue in SIP

Algorithm:
  1. Collect all topics the student has mastery data for.
  2. Score each unmastered topic by: weakness × impact weight.
  3. Impact weight = 1 + number of other topics that depend on this topic.
  4. Return top 3 as recommendations.
  5. Cold-start: if no mastery data, return first 3 topics in curriculum order.
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Topic recommendation engine based on SIP mastery map.

    Usage:
        engine = RecommendationEngine(user_id=42)
        recs = engine.get_recommendations(top_n=3)
    """

    def __init__(self, user_id):
        self.user_id = str(user_id)

    def get_recommendations(self, top_n: int = 3) -> List[Dict]:
        """
        Returns up to `top_n` topic recommendation dicts, each:
          {
            "topic_id": int,
            "title": str,
            "subject": str,
            "mastery_score": float,     # current 0-100
            "mastery_label": str,       # weak/developing/strong/mastered
            "priority_score": float,    # weakness × impact (higher = more urgent)
            "reason": str,
          }
        """
        from core.models import Topic, StudentIntelligenceProfile
        from django.contrib.auth import get_user_model

        try:
            User = get_user_model()
            user = User.objects.get(pk=int(self.user_id))
            sip, _ = StudentIntelligenceProfile.objects.get_or_create(user=user)
        except Exception as e:
            logger.error(f"[Recommendations] Could not load SIP: {e}")
            return []

        all_topics = list(Topic.objects.select_related('subject').prefetch_related('required_for'))

        # Cold-start: no mastery data → return first 3 topics in curriculum order
        if not sip.mastery_map:
            logger.info(f"[Recommendations] Cold-start for user={self.user_id}")
            return self._cold_start(all_topics, top_n)

        # Build impact weights: number of downstream topics that depend on each topic
        impact_weight: Dict[int, int] = {}
        for t in all_topics:
            downstream = t.required_for.count()
            impact_weight[t.pk] = 1 + downstream   # min weight 1

        # Score all topics
        scored = []
        for t in all_topics:
            score = sip.get_mastery_score(t.pk)
            label = sip.get_mastery_label(t.pk)

            if label == "mastered":
                continue    # Skip mastered topics

            weakness       = 100.0 - score             # 0 = strong, 100 = total beginner
            impact         = impact_weight.get(t.pk, 1)
            priority_score = weakness * impact

            reason = self._build_reason(score, label, impact)

            scored.append({
                "topic_id":      t.pk,
                "title":         t.title,
                "subject":       t.subject.name,
                "mastery_score": round(score, 1),
                "mastery_label": label,
                "priority_score": round(priority_score, 1),
                "reason":        reason,
            })

        # Sort by priority descending
        scored.sort(key=lambda x: x["priority_score"], reverse=True)

        recommendations = scored[:top_n]

        # Persist updated revision queue in SIP
        try:
            all_ids = [t.pk for t in all_topics]
            sip.recalculate_revision_queue(all_ids)
            sip.save(update_fields=["revision_priority_queue", "updated_at"])
        except Exception as e:
            logger.warning(f"[Recommendations] Could not save revision queue: {e}")

        logger.info(
            f"[Recommendations] user={self.user_id} | "
            f"top_recs={[r['title'] for r in recommendations]}"
        )
        return recommendations

    @staticmethod
    def _cold_start(all_topics, top_n: int) -> List[Dict]:
        """Return first `top_n` topics for brand-new students."""
        results = []
        for t in all_topics[:top_n]:
            results.append({
                "topic_id":      t.pk,
                "title":         t.title,
                "subject":       t.subject.name,
                "mastery_score": 0.0,
                "mastery_label": "weak",
                "priority_score": 100.0,
                "reason":        "Starting point — no prior study data yet.",
            })
        return results

    @staticmethod
    def _build_reason(score: float, label: str, impact: int) -> str:
        if label == "weak":
            base = f"Foundational gap — only {score:.0f}/100 mastery."
        elif label == "developing":
            base = f"Still developing — {score:.0f}/100. Consistent practice recommended."
        else:
            base = f"Almost there — {score:.0f}/100. A quick review will push you to mastery."

        if impact > 3:
            base += f" ({impact - 1} other topics depend on this.)"
        return base
