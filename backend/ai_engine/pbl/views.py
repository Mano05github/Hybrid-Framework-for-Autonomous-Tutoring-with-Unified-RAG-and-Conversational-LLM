"""
PBL REST API Views

Endpoints:
  POST /api/pbl/session/start/         → create PBLSession, return session_id + problem
  GET  /api/pbl/session/<id>/          → get session details
  GET  /api/pbl/graph/<subject_id>/    → subject concept graph for dashboard
"""

import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


class StartSessionView(APIView):
    """
    POST /api/pbl/session/start/
    Body: { "subject": "<slug_or_id>" }
    Returns: { "session_id": "...", "problem": {...} }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        subject_slug = (request.data.get('subject') or '').strip()
        topic_id     = request.data.get('topic_id')

        if not subject_slug and not topic_id:
            return Response({'error': 'subject or topic_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # 1. Resolve concept node — prefer direct topic_id
        concept = None
        if topic_id:
            from ai_engine.pbl.models import ConceptNode
            try:
                concept = ConceptNode.objects.select_related('topic__subject').get(
                    topic_id=int(topic_id)
                )
            except (ConceptNode.DoesNotExist, ValueError, TypeError):
                # ConceptNode may not exist yet; try subject fallback
                concept = None

        if concept is None:
            from ai_engine.pbl.concept_graph import get_concept_for_subject_slug
            concept = get_concept_for_subject_slug(subject_slug, user=user)

        if concept is None:
            # Last resort: auto-create a ConceptNode for this topic
            if topic_id:
                concept = _get_or_create_concept_for_topic(topic_id)

        if concept is None:
            return Response(
                {'error': f'No concept found for the selected topic. Please seed concept nodes first.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Generate problem
        from ai_engine.pbl.problem_generator import generate_problem
        spec = generate_problem(concept)

        if spec is None:
            return Response(
                {'error': 'Problem generation failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 3. Create PBLSession
        from ai_engine.pbl.models import PBLSession
        session = PBLSession.objects.create(
            user=user,
            concept=concept,
            subject=concept.subject,
            problem_title=spec.title,
            problem_statement=spec.statement,
            difficulty_level=spec.difficulty,
        )

        problem_data = {
            'title':         spec.title,
            'statement':     spec.statement,
            'concept_name':  spec.concept_name,
            'subject_name':  spec.subject_name,
            'difficulty':    spec.difficulty,
            'hints':         spec.hints,
            'tags':          spec.tags,
        }

        logger.info('[PBL] Session started: %s for user %s', session.id, user.id)

        return Response({
            'session_id': str(session.id),
            'problem':    problem_data,
        }, status=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    """
    GET /api/pbl/session/<session_id>/
    Returns session + mastery data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        from ai_engine.pbl.models import PBLSession
        try:
            session = PBLSession.objects.select_related(
                'concept__topic__subject', 'subject'
            ).get(pk=session_id, user=request.user)
        except PBLSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'session_id':    str(session.id),
            'status':        session.status,
            'mastery_score': session.mastery_score,
            'difficulty':    session.difficulty_level,
            'hint_count':    session.hint_count,
            'attempt_count': session.attempt_count,
            'problem': {
                'title':     session.problem_title,
                'statement': session.problem_statement,
                'concept':   session.concept.topic.title if session.concept else '',
                'subject':   session.subject.name if session.subject else '',
                'difficulty': session.difficulty_level,
            },
        })


class SubjectGraphView(APIView):
    """
    GET /api/pbl/graph/<subject_id>/
    Returns concept graph nodes + edges for the dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, subject_id):
        from ai_engine.pbl.concept_graph import build_subject_graph
        try:
            nodes = build_subject_graph(int(subject_id))
        except Exception as exc:
            logger.error('[PBL] Graph error: %s', exc)
            return Response({'error': 'Could not build concept graph.'}, status=500)

        return Response({'nodes': nodes})


# ── Module-level helpers ──────────────────────────────────────────────────────

def _get_or_create_concept_for_topic(topic_id) -> 'ConceptNode | None':
    """
    Auto-create a ConceptNode for a Topic that hasn't been seeded yet.
    Called as a last resort when topic_id is provided but no ConceptNode exists.
    """
    from ai_engine.pbl.models import ConceptNode
    from core.models import Topic
    from django.utils.text import slugify

    try:
        topic = Topic.objects.select_related('subject').get(pk=int(topic_id))
    except (Topic.DoesNotExist, ValueError):
        return None

    base_slug = slugify(topic.title)[:100]
    slug      = base_slug
    counter   = 1
    while ConceptNode.objects.filter(slug=slug).exclude(topic=topic).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    node, _ = ConceptNode.objects.get_or_create(
        topic=topic,
        defaults={
            'slug':        slug,
            'description': topic.description or '',
            'difficulty':  1,
            'is_active':   True,
        },
    )
    return node
