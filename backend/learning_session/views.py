from django.shortcuts import render
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ai_engine.gaps.coder_engine import SocraticCoderEngine
from learning_session.models import CodingProblem
from django.utils import timezone
from datetime import datetime
import asyncio
import uuid
import time


# ==================== Session Management Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request):
    """
    Start a new learning session
    
    POST /api/sessions/start/
    Body: {
        "topic": "Binary Search Trees" (optional)
    }
    
    Returns: {
        "id": "uuid-string",
        "session_id": "uuid-string",
        "started_at": "ISO timestamp"
    }
    """
    topic = request.data.get('topic', '')
    session_id = str(uuid.uuid4())
    
    # Store session info in Django session
    request.session[f'session_{session_id}'] = {
        'user_id': request.user.id,
        'topic': topic,
        'started_at': timezone.now().isoformat()
    }
    
    return Response({
        'id': session_id,
        'session_id': session_id,  # Compatibility with frontend
        'started_at': timezone.now().isoformat(),
        'topic': topic
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_session(request, session_id):
    """
    End a learning session
    
    POST /api/sessions/{session_id}/end/
    
    Returns: {
        "message": "Session ended",
        "duration_seconds": 1234
    }
    """
    session_key = f'session_{session_id}'
    session_data = request.session.get(session_key)
    
    if not session_data:
        return Response(
            {'error': 'Session not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculate duration
    started_at = datetime.fromisoformat(session_data['started_at'])
    if timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at)
    duration = (timezone.now() - started_at).total_seconds()
    
    # Clean up session
    del request.session[session_key]
    
    return Response({
        'message': 'Session ended successfully',
        'duration_seconds': int(duration)
    })


# ==================== Code Execution Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_code(request):
    """
    Execute Python code directly (for editor testing)
    
    POST /api/gaps/coding/execute/
    Body: {
        "code": "print('Hello')",
        "session_id": "uuid" (optional)
    }
    
    Returns: {
        "output": "Hello\\n",
        "error": null,
        "execution_time_ms": 45
    }
    """
    code = request.data.get('code')
    
    if not code:
        return Response(
            {'error': 'No code provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        start_time = time.time()
        
        # Use Gap 3's safe execution
        engine = SocraticCoderEngine()
        result = asyncio.run(engine._execute_code_safely(code, []))
        
        execution_time = int((time.time() - start_time) * 1000)
        
        if result['success']:
            output = result.get('stdout', '') or str(result.get('output', ''))
            return Response({
                'output': output if output else 'Code executed successfully (no output)',
                'error': None,
                'execution_time_ms': execution_time
            })
        else:
            return Response({
                'output': None,
                'error': result.get('error', 'Unknown error'),
                'execution_time_ms': execution_time
            })
    
    except Exception as e:
        return Response(
            {'error': f'Execution failed: {str(e)}', 'output': None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_hint(request):
    """
    Get a Socratic hint without full code submission
    
    POST /api/gaps/coding/hint/
    Body: {
        "problem_id": 1,
        "hint_level": 0,
        "session_id": "uuid" (optional)
    }
    
    Returns: {
        "hint_text": "Consider the base case...",
        "hint_level": 1,
        "hint": "Consider the base case..."
    }
    """
    problem_id = request.data.get('problem_id', 1)
    current_level = request.data.get('hint_level', 0)
    
    try:
        # Get problem
        problem = CodingProblem.objects.get(id=problem_id)
        
        # Generate hint at next level
        next_level = min(int(current_level) + 1, 5)
        
        engine = SocraticCoderEngine()
        hint_text = asyncio.run(engine._generate_approach_hint(
            level=next_level,
            problem=problem,
            code=""
        ))
        
        return Response({
            'hint_text': hint_text,
            'hint_level': next_level,
            'hint': hint_text  # Compatibility
        })
    
    except CodingProblem.DoesNotExist:
        # Return generic hint if problem not found
        generic_hints = [
            "💡 Think about the problem step by step. What's the first thing you need to do?",
            "💡 Consider the edge cases. What happens with empty inputs?",
            "💡 Break the problem into smaller sub-problems.",
            "💡 What data structure would be most efficient here?",
            "💡 Think about the time complexity. Can you optimize this?"
        ]
        next_level = min(int(current_level) + 1, 5)
        hint_text = generic_hints[min(next_level - 1, len(generic_hints) - 1)]
        
        return Response({
            'hint_text': hint_text,
            'hint_level': next_level,
            'hint': hint_text
        })
    
    except Exception as e:
        return Response(
            {'error': f'Hint generation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== Gap 3: Socratic Coder Endpoints ====================


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_code(request):
    """
    Submit code for Gap 3 Socratic analysis
    
    POST /api/submit-code/
    Body: {
        "problem_id": 1,
        "code": "def binary_search(arr, target):\n    ...",
        "time_spent": 240  # seconds
    }
    """
    problem_id = request.data.get('problem_id')
    code = request.data.get('code')
    time_spent = request.data.get('time_spent', 0)
    
    if not all([problem_id, code]):
        return Response(
            {"error": "Missing required fields: problem_id and code"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Run Gap 3 analysis
        engine = SocraticCoderEngine()
        result = asyncio.run(engine.analyze_code_submission(
            user_id=request.user.id,
            problem_id=int(problem_id),
            code=code,
            time_spent=int(time_spent),
            emotion_valence=0.0  # TODO: Get from Gap 4 empath agent
        ))
        
        return Response({
            "is_correct": result["is_correct"],
            "error_type": result["analysis"]["error_type"],
            "error_details": result["analysis"]["error_details"],
            "hint_level": result["hint_decision"]["hint_level"] if result["hint_decision"]["should_offer"] else None,
            "hint_text": result["hint_text"],
            "encouragement": result["encouragement"],
            "struggle_score": result["hint_decision"]["struggle_score"]
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Analysis failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_coding_profile(request):
    """
    Get student's coding profile for Gap 3
    
    GET /api/coding-profile/
    """
    from learning_session.models import StudentCodingProfile
    
    try:
        profile = StudentCodingProfile.objects.get(user=request.user)
        return Response({
            "skill_level": profile.skill_level,
            "problems_solved": profile.problems_solved,
            "avg_hint_level": profile.avg_hint_level,
            "quick_learner": profile.quick_learner,
            "common_error_types": profile.common_error_types
        }, status=status.HTTP_200_OK)
    except StudentCodingProfile.DoesNotExist:
        return Response({
            "message": "No profile found. Submit code to create one."
        }, status=status.HTTP_404_NOT_FOUND)


# ==================== Gap 4: Adaptive Empath Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_emotion_event(request):
    """
    Log an emotion event for Gap 4 analysis
    
    POST /api/gaps/emotion-log/
    Body: {
        "session_id": "uuid-string",
        "valence": -0.5,
        "intensity": "moderate",
        "pause_duration": 5.2,
        "sentiment_score": -0.6,
        "error_rate": 0.3,
        "trigger_type": "pause"
    }
    """
    from learning_session.models import EmotionEvent
    
    session_id = request.data.get('session_id')
    valence = request.data.get('valence', 0.0)
    intensity = request.data.get('intensity', 'mild')
    
    if not session_id:
        return Response(
            {"error": "Missing required field: session_id"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        event = EmotionEvent.objects.create(
            user=request.user,
            session_id=session_id,
            valence=float(valence),
            intensity=intensity,
            pause_duration=float(request.data.get('pause_duration', 0.0)),
            sentiment_score=float(request.data.get('sentiment_score', 0.0)),
            error_rate=float(request.data.get('error_rate', 0.0)),
            trigger_type=request.data.get('trigger_type', 'unknown'),
            intervention_applied=False,
            metadata=request.data.get('metadata', {})
        )
        
        return Response({
            "event_id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "message": "Emotion event logged successfully"
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to log emotion event: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teaching_strategy(request):
    """
    Get user's teaching strategy profile for Gap 4
    
    GET /api/gaps/teaching-strategy/
    """
    from learning_session.models import TeachingStrategy
    
    try:
        strategy = TeachingStrategy.objects.get(user=request.user)
        return Response({
            "preferred_modality": strategy.preferred_modality,
            "pace_preference": strategy.pace_preference,
            "intervention_threshold": strategy.intervention_threshold,
            "effective_interventions": strategy.effective_interventions,
            "pacing_success_rate": strategy.pacing_success_rate,
            "visualization_success_rate": strategy.visualization_success_rate,
            "branching_success_rate": strategy.branching_success_rate,
            "last_updated": strategy.last_updated.isoformat()
        }, status=status.HTTP_200_OK)
    except TeachingStrategy.DoesNotExist:
        return Response({
            "message": "No teaching strategy found. One will be created during sessions.",
            "default_modality": "text",
            "default_pace": 1.0
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_emotion_analytics(request):
    """
    Get emotion analytics for Gap 4 dashboard
    
    GET /api/gaps/emotion-analytics/?session_id=uuid&days=7
    """
    from learning_session.models import EmotionEvent, EmotionLog
    from django.utils import timezone
    from datetime import timedelta
    
    session_id = request.GET.get('session_id')
    days = int(request.GET.get('days', 7))
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Recent events
        events_query = EmotionEvent.objects.filter(
            user=request.user,
            timestamp__gte=cutoff_date
        )
        
        if session_id:
            events_query = events_query.filter(session_id=session_id)
        
        events = events_query.order_by('-timestamp')[:50]
        
        # Aggregated logs
        logs = EmotionLog.objects.filter(
            user=request.user,
            timestamp__gte=cutoff_date
        ).order_by('-timestamp')[:20]
        
        return Response({
            "events": [{
                "timestamp": event.timestamp.isoformat(),
                "valence": event.valence,
                "intensity": event.intensity,
                "trigger_type": event.trigger_type,
                "intervention_applied": event.intervention_applied
            } for event in events],
            "logs": [{
                "timestamp": log.timestamp.isoformat(),
                "emotion_level": log.emotion_level,
                "valence": log.valence,
                "intervention_type": log.intervention_type,
                "intervention_success": log.intervention_success
            } for log in logs],
            "summary": {
                "total_events": events_query.count(),
                "interventions_applied": events_query.filter(intervention_applied=True).count(),
                "avg_valence": events_query.aggregate(avg=models.Avg('valence'))['avg'] or 0.0
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to fetch analytics: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


