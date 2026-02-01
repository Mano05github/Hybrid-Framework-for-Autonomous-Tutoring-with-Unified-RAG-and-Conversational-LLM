from django.urls import path
from .views import ChatView
from .views_tts import generate_speech, get_available_speakers
from .views_stt import transcribe_audio

urlpatterns = [
    path('chat/', ChatView.as_view(), name='ai_chat'),
    path('tts/generate/', generate_speech, name='tts_generate'),
    path('tts/speakers/', get_available_speakers, name='tts_speakers'),
    path('stt/transcribe/', transcribe_audio, name='stt_transcribe'),
]
