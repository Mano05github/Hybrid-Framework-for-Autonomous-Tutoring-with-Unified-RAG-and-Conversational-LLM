"""
SIP & Recommendation REST Endpoints
=====================================
GET /api/ai/recommendations/   → top-N topic recommendations for the logged-in user
GET /api/ai/sip/               → full SIP snapshot (mastery, streaks, confidence, style)
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """
    Returns top-N (default 3) topic recommendations with mastery scores and
    reasoning labels (weakness, cold_start).

    Query params:
      ?n=<int>   — number of recommendations (1–10, default 3)
    """
    try:
        n = int(request.query_params.get("n", 3))
        n = max(1, min(n, 10))

        from .recommendation_engine import RecommendationEngine
        engine = RecommendationEngine(user_id=request.user.pk)
        recs = engine.get_recommendations(top_n=n)

        return Response({"recommendations": recs}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("[API] get_recommendations failed")
        return Response(
            {"error": "Could not generate recommendations.", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sip(request):
    """
    Returns a snapshot of the Student Intelligence Profile for the dashboard:
      - mastery_map          {topic_id: score}
      - dominant_style       visual | analytical | conceptual | pattern
      - style_weights        {visual, analytical, conceptual, pattern}
      - daily_streak         int
      - correct_streak       int
      - confidence_index     0.0 – 1.0
      - difficulty_tolerance 0.0 – 1.0
      - reinforcement_mode   bool
      - consecutive_wrong    int
      - revision_queue       [topic_id, ...]
      - total_sessions       int
    """
    try:
        from core.models import StudentIntelligenceProfile

        sip, _ = StudentIntelligenceProfile.objects.get_or_create(user=request.user)

        data = {
            "mastery_map":          sip.mastery_map or {},
            "dominant_style":       sip.dominant_learning_style(),
            "style_weights": {
                "visual":      sip.visual_weight,
                "analytical":  sip.analytical_weight,
                "conceptual":  sip.conceptual_weight,
                "pattern":     sip.pattern_weight,
            },
            "daily_streak":         sip.daily_streak,
            "correct_streak":       sip.correct_streak,
            "confidence_index":     round(float(sip.confidence_index), 4),
            "difficulty_tolerance": round(float(sip.difficulty_tolerance), 4),
            "reinforcement_mode":   sip.reinforcement_mode_active,
            "consecutive_wrong":    sip.consecutive_wrong_answers,
            "revision_queue":       sip.revision_priority_queue or [],
            "total_sessions":       sip.total_sessions,
        }
        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("[API] get_sip failed")
        return Response(
            {"error": "Could not load SIP.", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
