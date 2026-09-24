"""
Speech-to-Text engine using Deepgram only.

Accepts WebM audio directly from browser MediaRecorder.
Built-in noise rejection via confidence + post-processing filter.
"""

import os
import re
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Noise words / filler patterns that should be discarded
_NOISE_PATTERNS = re.compile(
    r'^[\s\.,!?\-_\(\)\[\]]{0,5}$'
    r'|^\[.*?\]$'
    r'|^(uh+|um+|mm+|hmm+|ah+|oh+|hm+|er+)$',
    re.IGNORECASE,
)


class STTEngine:
    """
    Singleton Speech-to-Text engine using Deepgram only.
    """

    _instance    = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._deepgram_key = os.getenv('DEEPGRAM_API_KEY')
        self._provider = 'deepgram'
        self._model = 'nova-2'

        if not self._deepgram_key:
            raise ValueError('DEEPGRAM_API_KEY is required in backend/.env')

        self._initialized = True
        logger.info('STT initialized: provider=%s model=%s', self._provider, self._model)

    # -- Public API (backward-compatible signature) ----------------------------

    def transcribe_audio(
        self,
        audio_content: bytes,
        language_code: Optional[str] = None,
        sample_rate: int = 16000,
        encoding=None,
    ) -> Optional[str]:
        """
        Transcribe audio bytes to text.
        Returns cleaned transcript string, or None for non-speech audio.
        """
        if not audio_content or len(audio_content) < 512:
            return None

        try:
            raw = self._transcribe_with_deepgram(audio_content)
            return self._clean(raw)

        except Exception as exc:
            logger.error('STT transcription error: %s', exc, exc_info=True)
            return None

    # -- Streaming shim --------------------------------------------------------

    def transcribe_streaming(self, audio_generator, language_code: str = 'en-US'):
        """Yields single transcript chunk for backward-compat."""
        try:
            chunks = list(audio_generator)
            if chunks:
                result = self.transcribe_audio(b''.join(chunks))
                if result:
                    yield result
        except Exception as exc:
            logger.error('STT streaming error: %s', exc, exc_info=True)

    # -- Internal helpers ------------------------------------------------------

    def _clean(self, text: str) -> Optional[str]:
        """Strip noise tokens; return None if nothing useful remains."""
        if not text:
            return None
        if _NOISE_PATTERNS.search(text):
            return None
        if len(re.findall(r'\w', text)) < 2:
            return None
        return text

    def _transcribe_with_deepgram(self, audio_content: bytes) -> Optional[str]:
        params = {
            'model': 'nova-2',
            'smart_format': 'true',
            'punctuate': 'true',
            'detect_language': 'true',
            'filler_words': 'false',
            'numerals': 'true',
        }
        response = requests.post(
            'https://api.deepgram.com/v1/listen',
            params=params,
            headers={
                'Authorization': f'Token {self._deepgram_key}',
                'Content-Type': 'audio/webm',
            },
            data=audio_content,
            timeout=30,
        )
        if not response.ok:
            # Deepgram sends useful validation hints in the response body.
            logger.error(
                'Deepgram STT request failed: status=%s url=%s body=%s',
                response.status_code,
                response.url,
                response.text,
            )
        response.raise_for_status()
        payload = response.json()
        alt = (((payload.get('results') or {}).get('channels') or [{}])[0].get('alternatives') or [{}])[0]
        transcript = (alt.get('transcript') or '').strip()
        confidence = alt.get('confidence') or 0.0
        if confidence < 0.45:
            return None
        return transcript or None


def get_stt_engine() -> STTEngine:
    """Get or create the singleton STT engine."""
    return STTEngine()
