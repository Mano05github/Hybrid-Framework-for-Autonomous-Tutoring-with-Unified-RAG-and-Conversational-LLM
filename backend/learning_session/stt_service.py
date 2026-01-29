import speech_recognition as sr
import os
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        logger.info("STT Service Initialized (Google Web Speech API)")

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes audio file to text using Google Speech Recognition.
        """
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                
            # Use Google Web Speech API (Free, connection required)
            text = self.recognizer.recognize_google(audio_data)
            logger.info(f"STT Transcription: {text}")
            return text
            
        except sr.UnknownValueError:
            logger.warning("STT: Speech not recognized")
            return None
        except sr.RequestError as e:
            logger.error(f"STT Service Error: {e}")
            return None
        except Exception as e:
            logger.error(f"STT Unexpected Error: {e}")
            return None
