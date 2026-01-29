"""
Analytics API Views for Dashboard
Provides endpoints for student performance tracking and statistics
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Min, Max, Q
from datetime import datetime, timedelta
from .models import (
    CodeSubmission, 
    CodingProblem, 
    VisionaryMetric, 
    VisionaryForecast,
    EmotionLog,
    StudentCodingProfile
)
from core.models import Topic, UserProgress


@csrf_exempt
@require_http_methods(["GET"])
def get_today_stats(request):
    """
    GET /api/sessions/stats/today/
    Returns today's performance metrics
    """
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        today = timezone.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_start = timezone.make_aware(today_start)
        
        # Problems solved today
        problems_solved = CodeSubmission.objects.filter(
            user=user,
            submitted_at__gte=today_start,
            is_correct=True
        ).values('problem').distinct().count()
        
        # Time spent today (from VisionaryMetric)
        time_spent_seconds = VisionaryMetric.objects.filter(
            user=user,
            timestamp__gte=today_start
        ).aggregate(
            total_time=Sum('completion_time')
        )['total_time'] or 0
        
        time_spent_minutes = int(time_spent_seconds / 60) if time_spent_seconds else 0
        
        # Mastery gained today (calculate from forecasts)
        today_forecasts = VisionaryForecast.objects.filter(
            user=user,
            forecast_date=today
        )
        
        mastery_gained = 0
        if today_forecasts.exists():
            # Average mastery increase across topics
            mastery_values = [f.current_mastery for f in today_forecasts]
            mastery_gained = int((sum(mastery_values) / len(mastery_values)) * 100) if mastery_values else 0
        
        # Topics studied today
        topics_studied = VisionaryMetric.objects.filter(
            user=user,
            timestamp__gte=today_start
        ).exclude(current_topic='').values('current_topic').distinct().count()
        
        return JsonResponse({
            "problemsSolved": problems_solved,
            "timeSpent": time_spent_minutes,
            "masteryGained": mastery_gained,
            "topicsStudied": topics_studied
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_weekly_trend(request):
    """
    GET /api/sessions/stats/weekly/
    Returns 7-day mastery trend data
    """
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Get last 7 days
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        
        # Build day labels
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        trend_data = []
        
        for i in range(7):
            current_date = seven_days_ago + timedelta(days=i)
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            day_start = timezone.make_aware(day_start)
            day_end = timezone.make_aware(day_end)
            
            # Get average mastery for this day from forecasts
            day_forecasts = VisionaryForecast.objects.filter(
                user=user,
                forecast_date=current_date
            )
            
            if day_forecasts.exists():
                avg_mastery = day_forecasts.aggregate(
                    avg=Avg('current_mastery')
                )['avg'] or 0
                mastery_percentage = int(avg_mastery * 100)
            else:
                # Use baseline from previous day or default to 65
                if i > 0 and trend_data:
                    mastery_percentage = trend_data[-1]['mastery']
                else:
                    mastery_percentage = 65
            
            trend_data.append({
                "day": days[current_date.weekday()],
                "mastery": mastery_percentage
            })
        
        return JsonResponse({"trend": trend_data})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_recent_sessions(request):
    """
    GET /api/sessions/recent/
    Returns last 10 learning sessions
    """
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Get distinct sessions from VisionaryMetric
        sessions_query = VisionaryMetric.objects.filter(
            user=user
        ).values('session_id', 'current_topic').annotate(
            earliest=Min('timestamp'),
            latest=Max('timestamp'),
            error_count=Sum('error_count')
        ).order_by('-earliest')[:10]
        
        sessions = []
        for session_data in sessions_query:
            session_id = session_data['session_id']
            topic = session_data['current_topic'] or 'General Learning'
            
            # Calculate duration
            earliest = session_data['earliest']
            latest = session_data['latest']
            duration_seconds = (latest - earliest).total_seconds() if earliest and latest else 0
            duration_minutes = int(duration_seconds / 60)
            
            # Count problems solved in this session
            problems_solved = CodeSubmission.objects.filter(
                user=user,
                submitted_at__range=(earliest, latest),
                is_correct=True
            ).values('problem').distinct().count()
            
            # Format timestamp
            time_diff = timezone.now() - earliest
            if time_diff.days > 0:
                timestamp = f"{time_diff.days} days ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                timestamp = f"{hours} hours ago"
            else:
                minutes = time_diff.seconds // 60
                timestamp = f"{minutes} minutes ago"
            
            sessions.append({
                "id": session_id,
                "topic": topic,
                "duration": f"{duration_minutes}m",
                "problemsSolved": problems_solved,
                "timestamp": timestamp
            })
        
        return JsonResponse({"sessions": sessions})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_overall_stats(request):
    """
    GET /api/sessions/stats/overall/
    Returns cumulative statistics
    """
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Total topics covered
        total_topics = VisionaryMetric.objects.filter(
            user=user
        ).exclude(current_topic='').values('current_topic').distinct().count()
        
        # Total problems solved
        total_problems = CodeSubmission.objects.filter(
            user=user,
            is_correct=True
        ).values('problem').distinct().count()
        
        # Total hours (from all VisionaryMetric entries)
        total_seconds = VisionaryMetric.objects.filter(
            user=user
        ).aggregate(
            total=Sum('completion_time')
        )['total'] or 0
        
        total_hours = int(total_seconds / 3600) if total_seconds else 0
        
        # Calculate current streak
        current_streak = calculate_streak(user)
        
        return JsonResponse({
            "totalTopics": total_topics,
            "totalProblems": total_problems,
            "totalHours": total_hours,
            "currentStreak": current_streak
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_active_session(request):
    """
    GET /api/sessions/active/
    Checks if user has an active learning session (within last 4 hours)
    """
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        four_hours_ago = timezone.now() - timedelta(hours=4)
        
        # Check for recent activity
        recent_metric = VisionaryMetric.objects.filter(
            user=user,
            timestamp__gte=four_hours_ago
        ).order_by('-timestamp').first()
        
        if recent_metric:
            return JsonResponse({
                "hasActiveSession": True,
                "session": {
                    "id": recent_metric.session_id,
                    "topic": recent_metric.current_topic or 'General Learning',
                    "startedAt": recent_metric.timestamp.isoformat()
                }
            })
        else:
            return JsonResponse({
                "hasActiveSession": False,
                "session": None
            })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_available_topics(request):
    """
    GET /api/topics/available/
    Returns list of available topics with mastery percentages
    """
    try:
        user = request.user if request.user.is_authenticated else None
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Get all topics from core
        topics_query = Topic.objects.all().prefetch_related('subject')
        
        topics = []
        for topic in topics_query:
            # Get latest mastery forecast for this topic
            latest_forecast = VisionaryForecast.objects.filter(
                user=user,
                topic=topic.title
            ).order_by('-forecast_date').first()
            
            mastery = int(latest_forecast.current_mastery * 100) if latest_forecast else 0
            
            # Determine category (from subject)
            category = topic.subject.name if topic.subject else 'General'
            
            # Simple difficulty estimation based on topic order
            if topic.order < 5:
                difficulty = 'easy'
            elif topic.order < 10:
                difficulty = 'medium'
            else:
                difficulty = 'hard'
            
            # Simple prerequisite logic (topic before this one)
            prerequisite = ''
            if topic.order > 1:
                prev_topic = Topic.objects.filter(
                    subject=topic.subject,
                    order=topic.order - 1
                ).first()
                if prev_topic:
                    prerequisite = prev_topic.title
            
            # Lock if prerequisite exists and mastery < 70%
            is_locked = False
            if prerequisite:
                prereq_forecast = VisionaryForecast.objects.filter(
                    user=user,
                    topic=prerequisite
                ).order_by('-forecast_date').first()
                
                if prereq_forecast:
                    prereq_mastery = prereq_forecast.current_mastery * 100
                    is_locked = prereq_mastery < 70
                else:
                    is_locked = True  # No data means not started
            
            topics.append({
                "id": topic.id,
                "name": topic.title,
                "category": category,
                "difficulty": difficulty,
                "mastery": mastery,
                "prerequisite": prerequisite,
                "isLocked": is_locked
            })
        
        return JsonResponse({"topics": topics})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def calculate_streak(user):
    """Calculate current learning streak in days"""
    try:
        today = timezone.now().date()
        streak = 0
        current_date = today
        
        # Check backwards from today
        while True:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            day_start = timezone.make_aware(day_start)
            day_end = timezone.make_aware(day_end)
            
            # Check if user had activity on this day
            has_activity = VisionaryMetric.objects.filter(
                user=user,
                timestamp__range=(day_start, day_end)
            ).exists()
            
            if has_activity:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
            
            # Prevent infinite loop (max 365 days streak)
            if streak >= 365:
                break
        
        return streak
        
    except Exception:
        return 0
