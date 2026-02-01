"""
Google Cloud Speech-to-Text Engine
Handles audio transcription using Google Cloud STT API
"""
import os
from typing import Optional
from google.cloud import speech
from django.conf import settings


class STTEngine:
    """Singleton Speech-to-Text Engine"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Set credentials path
        credentials_path = os.path.join(
            settings.BASE_DIR, 
            'config', 
            'google-cloud-credentials.json'
        )
        
        if os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            self.client = speech.SpeechClient()
            self._initialized = True
            print(f"✓ Google Cloud STT initialized with credentials from {credentials_path}")
        else:
            raise FileNotFoundError(
                f"Google Cloud credentials not found at {credentials_path}. "
                "Please ensure google-cloud-credentials.json exists in backend/config/"
            )
    
    def transcribe_audio(
        self, 
        audio_content: bytes, 
        language_code: str = "en-US",
        sample_rate: int = 16000,
        encoding: speech.RecognitionConfig.AudioEncoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
    ) -> Optional[str]:
        """
        Transcribe audio bytes to text using Google Cloud STT
        
        Args:
            audio_content: Raw audio bytes
            language_code: BCP-47 language code (default: en-US)
            sample_rate: Audio sample rate in Hz (default: 16000)
            encoding: Audio encoding format (default: LINEAR16/PCM)
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            audio = speech.RecognitionAudio(content=audio_content)
            
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="default",  # Can be changed to 'phone_call', 'video', 'command_and_search'
            )
            
            # Synchronous recognition for short audio (<1 minute)
            response = self.client.recognize(config=config, audio=audio)
            
            # Combine all transcripts
            transcripts = []
            for result in response.results:
                if result.alternatives:
                    transcripts.append(result.alternatives[0].transcript)
            
            return " ".join(transcripts) if transcripts else None
            
        except Exception as e:
            print(f"❌ STT Error: {str(e)}")
            return None
    
    def transcribe_streaming(self, audio_generator, language_code: str = "en-US"):
        """
        Streaming transcription for real-time audio
        
        Args:
            audio_generator: Generator yielding audio chunks
            language_code: BCP-47 language code
            
        Yields:
            Transcribed text chunks
        """
        try:
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True  # Get partial results
            )
            
            # Generator that yields audio requests
            def request_generator():
                yield speech.StreamingRecognizeRequest(audio_content=None)
                for chunk in audio_generator:
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
            
            responses = self.client.streaming_recognize(
                config=streaming_config,
                requests=request_generator()
            )
            
            for response in responses:
                for result in response.results:
                    if result.alternatives:
                        yield result.alternatives[0].transcript
                        
        except Exception as e:
            print(f"❌ Streaming STT Error: {str(e)}")
            yield None


# Singleton instance getter
def get_stt_engine() -> STTEngine:
    """Get or create the STT engine singleton"""
    return STTEngine()
