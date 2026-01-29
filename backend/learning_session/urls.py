"""URL configuration for learning_session app (Gap implementations)"""
from django.urls import path
from . import views
from .views_analytics import (
    get_today_stats,
    get_weekly_trend,
    get_recent_sessions,
    get_overall_stats,
    get_active_session,
    get_available_topics
)

urlpatterns = [
    # Session management
    path('start/', views.start_session, name='start_session'),
    path('<str:session_id>/end/', views.end_session, name='end_session'),
    
    # Gap 3: Code execution and hints
    path('gaps/coding/execute/', views.execute_code, name='execute_code'),
    path('gaps/coding/hint/', views.get_hint, name='get_hint'),
    
    # Gap 3: Socratic Coder endpoints
    path('submit-code/', views.submit_code, name='submit_code'),
    path('coding-profile/', views.get_coding_profile, name='coding_profile'),
    
    # Gap 4: Adaptive Empath endpoints
    path('emotion-log/', views.log_emotion_event, name='log_emotion_event'),
    path('teaching-strategy/', views.get_teaching_strategy, name='teaching_strategy'),
    path('emotion-analytics/', views.get_emotion_analytics, name='emotion_analytics'),
    
    # Analytics endpoints for dashboard
    path('stats/today/', get_today_stats, name='stats_today'),
    path('stats/weekly/', get_weekly_trend, name='stats_weekly'),
    path('recent/', get_recent_sessions, name='recent_sessions'),
    path('stats/overall/', get_overall_stats, name='stats_overall'),
    path('active/', get_active_session, name='active_session'),
]
