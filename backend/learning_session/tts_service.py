import asyncio
import edge_tts
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, voice="en-US-ChristopherNeural"):
        self.voice = voice # Professional male voice. Options: en-US-AriaNeural, en-GB-SoniaNeural
        logger.info(f"TTS Service initialized with voice: {self.voice}")

    async def generate_audio(self, text):
        """
        Generates MP3 audio bytes from text using Edge TTS.
        """
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            logger.info(f"Generated TTS Audio: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            logger.error(f"TTS Generation Failed: {e}")
            return None
