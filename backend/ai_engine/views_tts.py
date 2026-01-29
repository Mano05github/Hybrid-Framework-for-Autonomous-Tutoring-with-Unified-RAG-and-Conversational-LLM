"""
TTS API views for generating speech from text
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from ai_engine.tts import get_tts_engine

@csrf_exempt
@require_http_methods(["POST"])
def generate_speech(request):
    """
    Generate speech audio from text
    
    POST /api/tts/generate/
    Body: {
        "text": "I am waiting for you",
        "language": "en"  // optional, defaults to "en"
    }
    
    Returns: Audio file (WAV format) with Content-Type: audio/wav
    """
    try:
        # Parse request body
        if not request.body:
            return JsonResponse(
                {'error': 'Empty request body'},
                status=400
            )
        
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            return JsonResponse(
                {'error': f'Invalid JSON: {str(e)}'},
                status=400
            )
        
        text = data.get('text', '').strip()
        language = data.get('language', 'en')
        
        if not text:
            return JsonResponse(
                {'error': 'Text parameter is required'},
                status=400
            )
        
        # Get TTS engine
        tts_engine = get_tts_engine()
        
        # Generate speech
        audio_data = tts_engine.generate_speech(text, language)
        
        # Return audio as WAV
        response = HttpResponse(audio_data, content_type='audio/wav')
        response['Content-Disposition'] = 'inline; filename="speech.wav"'
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        
        return response
        
    except ValueError as e:
        return JsonResponse(
            {'error': str(e)},
            status=400
        )
    except RuntimeError as e:
        return JsonResponse(
            {'error': f'TTS generation failed: {str(e)}'},
            status=500
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'Internal server error: {str(e)}'},
            status=500
        )


@require_http_methods(["GET"])
def get_available_speakers(request):
    """
    Get list of available speakers (for multi-speaker models)
    
    GET /api/tts/speakers/
    
    Returns: {"speakers": ["speaker1", "speaker2", ...]}
    """
    try:
        tts_engine = get_tts_engine()
        speakers = tts_engine.get_available_speakers()
        
        return JsonResponse({
            'speakers': speakers,
            'count': len(speakers)
        })
        
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )
