from django.urls import path
from .views import ChatView, PBLRuntimeStatsView
from .views_tts import generate_speech, get_available_speakers
from .views_stt import transcribe_audio
from .views_sip import get_recommendations, get_sip

urlpatterns = [
    path('chat/', ChatView.as_view(), name='ai_chat'),
    path('stats/pbl-runtime/', PBLRuntimeStatsView.as_view(), name='pbl_runtime_stats'),
    path('tts/generate/', generate_speech, name='tts_generate'),
    path('tts/speakers/', get_available_speakers, name='tts_speakers'),
    path('stt/transcribe/', transcribe_audio, name='stt_transcribe'),
    # SIP & Recommendations
    path('recommendations/', get_recommendations, name='ai_recommendations'),
    path('sip/', get_sip, name='ai_sip'),
]
