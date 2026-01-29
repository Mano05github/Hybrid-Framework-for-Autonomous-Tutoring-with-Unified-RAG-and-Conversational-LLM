"""
Text-to-Speech engine using Google Cloud Text-to-Speech
Provides voice synthesis for the Vaathiyar agent
"""

import os
from google.cloud import texttospeech
from django.conf import settings
from typing import Optional

class TTSEngine:
    """Google Cloud TTS engine wrapper for generating speech from text"""
    
    _instance: Optional['TTSEngine'] = None
    
    def __init__(self):
        """Initialize the Google Cloud TTS client"""
        try:
            # Set credentials path
            credentials_path = os.path.join(
                settings.BASE_DIR, 
                'config', 
                'google-tts-credentials.json'
            )
            
            if os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            # Initialize the Text-to-Speech client
            self.client = texttospeech.TextToSpeechClient()
            
            # Default voice configuration - high-quality female voice
            self.voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-F",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            # Audio configuration - WAV format at 22050 Hz
            self.audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=1.0,
                pitch=0.0,
                sample_rate_hertz=22050
            )
            
            print(f"✓ Google Cloud TTS initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Google Cloud TTS: {e}")
            self.client = None
    
    @classmethod
    def get_instance(cls) -> 'TTSEngine':
        """Get singleton instance of TTS engine"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def generate_speech(
        self, 
        text: str, 
        language: str = "en",
        speaker: Optional[str] = None
    ) -> bytes:
        """
        Generate speech audio from text using Google Cloud TTS
        
        Args:
            text: Input text to synthesize
            language: Language code (e.g., 'en', 'ta')
            speaker: Optional voice name (e.g., 'en-US-Neural2-F')
        
        Returns:
            Audio data as bytes (WAV format)
        
        Raises:
            ValueError: If TTS client not initialized
            RuntimeError: If synthesis fails
        """
        if self.client is None:
            raise ValueError("Google Cloud TTS client not initialized")
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Use custom voice if specified, otherwise use default
            voice_params = self.voice
            if speaker:
                voice_params = texttospeech.VoiceSelectionParams(
                    language_code=f"{language}-US",
                    name=speaker
                )
            elif language != "en":
                # Adjust language if not English
                voice_params = texttospeech.VoiceSelectionParams(
                    language_code=f"{language}-US" if language == "en" else language,
                    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
                )
            
            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=self.audio_config
            )
            
            # Return the audio content as bytes
            return response.audio_content
            
        except Exception as e:
            raise RuntimeError(f"Google Cloud TTS synthesis failed: {e}")
    
    def get_available_speakers(self) -> list:
        """Get list of available voices from Google Cloud TTS"""
        if self.client is None:
            return []
        
        try:
            # Fetch available voices
            voices = self.client.list_voices()
            
            # Filter for English voices
            english_voices = [
                voice.name 
                for voice in voices.voices 
                if 'en-US' in voice.name
            ]
            
            return english_voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []


# Global instance getter
def get_tts_engine() -> TTSEngine:
    """Get the global TTS engine instance"""
    return TTSEngine.get_instance()
