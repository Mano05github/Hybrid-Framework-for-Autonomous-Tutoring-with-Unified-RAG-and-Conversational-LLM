from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubjectViewSet, TopicViewSet, LessonViewSet, QuizViewSet,
    UserProgressViewSet, DashboardView,
    SubjectLearnStatsView, SubjectTopicsStatsView,
)

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'topics', TopicViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'progress', UserProgressViewSet, basename='progress')

urlpatterns = [
    # Custom views must come BEFORE router.urls to avoid pk-conflict on 'subjects/learn-stats/'
    path('subjects/learn-stats/',              SubjectLearnStatsView.as_view(),   name='subject-learn-stats'),
    path('subjects/<int:pk>/topics-stats/',    SubjectTopicsStatsView.as_view(),  name='subject-topics-stats'),
    path('', include(router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
