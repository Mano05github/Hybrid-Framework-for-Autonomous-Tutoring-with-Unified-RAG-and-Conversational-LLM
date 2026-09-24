"""
ElevenLabs Speech-to-Text API views
"""
import base64

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .stt import get_stt_engine


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe_audio(request):
    """
    Transcribe audio to text using ElevenLabs Scribe v1.

    Request body:
    {
        "audio": "<base64_encoded_audio_data>"   # WebM/OPUS from browser
    }

    Response:
    {
        "text":    "transcribed text",
        "success": true
    }

    Note: language, sampleRate, encoding params no longer needed —
    ElevenLabs auto-detects language (Tamil and English supported).
    """
    try:
        audio_b64 = request.data.get('audio')
        if not audio_b64:
            return Response(
                {'error': 'Missing audio data'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            return Response(
                {'error': f'Invalid base64 audio: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Transcribe with ElevenLabs
        stt_engine = get_stt_engine()
        text = stt_engine.transcribe_audio(audio_bytes)

        if text:
            return Response({'text': text, 'success': True})
        else:
            return Response(
                {'error': 'Transcription failed — no speech detected'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
