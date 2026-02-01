"""
Google Cloud Speech-to-Text API views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from google.cloud import speech
import base64

from .stt import get_stt_engine


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe_audio(request):
    """
    Transcribe audio to text using Google Cloud STT
    
    Request body:
    {
        "audio": "base64_encoded_audio_data",
        "language": "en-US" (optional),
        "sampleRate": 16000 (optional),
        "encoding": "LINEAR16" (optional)
    }
    
    Response:
    {
        "text": "transcribed text",
        "success": true
    }
    """
    try:
        # Get audio data
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
        
        # Get optional parameters
        language_code = request.data.get('language', 'en-US')
        sample_rate = int(request.data.get('sampleRate', 16000))
        encoding_str = request.data.get('encoding', 'LINEAR16')
        
        # Map encoding string to enum
        encoding_map = {
            'LINEAR16': speech.RecognitionConfig.AudioEncoding.LINEAR16,
            'FLAC': speech.RecognitionConfig.AudioEncoding.FLAC,
            'MULAW': speech.RecognitionConfig.AudioEncoding.MULAW,
            'AMR': speech.RecognitionConfig.AudioEncoding.AMR,
            'AMR_WB': speech.RecognitionConfig.AudioEncoding.AMR_WB,
            'OGG_OPUS': speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            'WEBM_OPUS': speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        }
        encoding = encoding_map.get(encoding_str, speech.RecognitionConfig.AudioEncoding.LINEAR16)
        
        # Transcribe
        stt_engine = get_stt_engine()
        text = stt_engine.transcribe_audio(
            audio_content=audio_bytes,
            language_code=language_code,
            sample_rate=sample_rate,
            encoding=encoding
        )
        
        if text:
            return Response({
                'text': text,
                'success': True
            })
        else:
            return Response(
                {'error': 'Transcription failed - no speech detected'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
