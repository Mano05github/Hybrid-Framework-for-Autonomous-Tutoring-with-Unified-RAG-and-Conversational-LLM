from rest_framework import viewsets, permissions
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

from rest_framework.views import APIView
from rest_framework.response import Response
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
