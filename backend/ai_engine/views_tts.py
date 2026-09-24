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
    Generate speech audio from text using ElevenLabs TTS.

    POST /api/tts/generate/
    Body: {
        "text":     "Hello from Vaathiyar",
        "language": "en",          // optional (ignored, ElevenLabs auto-detects)
        "agent":    "teacher"      // optional: teacher|coder|examiner|supervisor|default
    }

    Returns: MP3 audio with Content-Type: audio/mpeg
    """
    try:
        if not request.body:
            return JsonResponse({'error': 'Empty request body'}, status=400)

        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)

        text   = data.get('text', '').strip()
        agent  = data.get('agent', 'default')
        language = data.get('language', 'en')   # kept for backward compat

        if not text:
            return JsonResponse({'error': 'Text parameter is required'}, status=400)

        tts_engine = get_tts_engine()
        audio_data = tts_engine.generate_speech(text, language=language, agent=agent)

        # ElevenLabs returns MP3 — update Content-Type accordingly
        response = HttpResponse(audio_data, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="speech.mp3"'
        response['Cache-Control'] = 'public, max-age=3600'

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
