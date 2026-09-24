from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Subject, Topic, Lesson, Quiz, UserProgress
from .serializers import (
    SubjectSerializer, TopicSerializer, LessonSerializer, 
    QuizSerializer, UserProgressSerializer
)

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Subjects.
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.AllowAny] # Open for now

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Topics.
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]

class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]

class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.AllowAny]

class UserProgressViewSet(viewsets.ModelViewSet):
    """
    Manage user progress. Only accessible by authenticated users.
    """
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from rest_framework import status
import random

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Stats Logic (Mocked + Real)
        completed_lessons = UserProgress.objects.filter(user=user, completed=True).count()
        total_time = "12.5 hrs" # Placeholder until we track time
        streak = "3 days" # Placeholder
        
        # Recommendations (Linking to our new RAG content)
        # In future, use dot product of user history vs topic embeddings
        suggested_topic = None
        algo_topic = Topic.objects.filter(title__icontains="Algorithms").first()
        if algo_topic:
            suggested_topic = {
                "id": algo_topic.id,
                "title": algo_topic.title,
                "subject": algo_topic.subject.name,
                "color": "blue"
            }
        
        return Response({
            "greeting": f"Welcome back, {user.first_name or user.username}!",
            "stats": {
                "time_spent": total_time,
                "lessons_completed": f"{completed_lessons} / 24",
                "streak": streak
            },
            "recent_activity": {
                "title": "Trigonometric Ratios", # Placeholder
                "category": "Mathematics • Intermediate",
                "progress": 45
            },
            "recommendation": suggested_topic
        })


# ─────────────────────────────────────────────────────────────────────────────
# Subject Learn Stats — powers the Learn page subject cards
# ─────────────────────────────────────────────────────────────────────────────

class SubjectLearnStatsView(APIView):
    """
    GET /api/core/subjects/learn-stats/
    Returns all subjects enriched with per-user completion stats and SIP mastery.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Pull SIP if it exists
        try:
            sip = user.sip
            mastery_map = sip.mastery_map or {}
            revision_queue = set(str(t) for t in (sip.revision_priority_queue or []))
        except Exception:
            mastery_map = {}
            revision_queue = set()

        subjects = Subject.objects.all()
        total_topics_all = 0
        completed_topics_all = 0
        results = []

        for s in subjects:
            topic_ids = list(Topic.objects.filter(subject=s).values_list('id', flat=True))
            topic_count = len(topic_ids)

            # Distinct topics where the user has completed ≥1 lesson
            completed_topic_count = UserProgress.objects.filter(
                user=user,
                lesson__topic__subject=s,
                completed=True
            ).values('lesson__topic').distinct().count()

            # Average Elo for topics in this subject (ignore topics with no Elo entry)
            elos = [mastery_map[str(tid)] for tid in topic_ids if str(tid) in mastery_map]
            if elos:
                mastery_pct = round(min(100, max(0, (sum(elos) / len(elos)) / 2000 * 100)))
            else:
                mastery_pct = 0

            has_recommended = any(str(tid) in revision_queue for tid in topic_ids)

            total_topics_all += topic_count
            completed_topics_all += completed_topic_count

            results.append({
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'topic_count': topic_count,
                'completed_topic_count': completed_topic_count,
                'mastery_pct': mastery_pct,
                'has_recommended': has_recommended,
            })

        global_pct = round(completed_topics_all / total_topics_all * 100) if total_topics_all else 0
        return Response({'global_pct': global_pct, 'subjects': results})


# ─────────────────────────────────────────────────────────────────────────────
# Subject Topics Stats — powers the Subject Hub page
# ─────────────────────────────────────────────────────────────────────────────

def _infer_difficulty(order: int) -> str:
    """Infer difficulty from topic order within its subject."""
    if order <= 2:
        return 'beginner'
    if order <= 5:
        return 'intermediate'
    return 'advanced'


class SubjectTopicsStatsView(APIView):
    """
    GET /api/core/subjects/<pk>/topics-stats/
    Optional query param: ?difficulty=beginner|intermediate|advanced
    Returns subject info, subject-level completion %, and all enriched topics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = request.user

        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            sip = user.sip
            mastery_map = sip.mastery_map or {}
            revision_queue = set(str(t) for t in (sip.revision_priority_queue or []))
        except Exception:
            mastery_map = {}
            revision_queue = set()

        # Subject-level completion (by lessons)
        total_lessons = Lesson.objects.filter(topic__subject=subject).count()
        completed_lessons = UserProgress.objects.filter(
            user=user, lesson__topic__subject=subject, completed=True
        ).count()
        subject_pct = round(completed_lessons / total_lessons * 100) if total_lessons else 0

        topics = Topic.objects.filter(subject=subject).order_by('order')
        difficulty_filter = (request.query_params.get('difficulty') or '').lower()

        topic_results = []
        for t in topics:
            difficulty = _infer_difficulty(t.order)
            if difficulty_filter and difficulty != difficulty_filter:
                continue

            lesson_count = Lesson.objects.filter(topic=t).count()
            completed_count = UserProgress.objects.filter(
                user=user, lesson__topic=t, completed=True
            ).count()
            completion_pct = round(completed_count / lesson_count * 100) if lesson_count else 0

            elo = mastery_map.get(str(t.id), 0)
            mastery_pct = round(min(100, max(0, elo / 2000 * 100))) if elo else 0

            topic_results.append({
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'order': t.order,
                'difficulty': difficulty,
                'lesson_count': lesson_count,
                'completed_lesson_count': completed_count,
                'completion_pct': completion_pct,
                'mastery_pct': mastery_pct,
                'is_recommended': str(t.id) in revision_queue,
            })

        return Response({
            'subject': {
                'id': subject.id,
                'name': subject.name,
                'description': subject.description,
            },
            'subject_pct': subject_pct,
            'topics': topic_results,
        })
