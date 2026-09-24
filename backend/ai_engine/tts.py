"""
Text-to-Speech engine using Deepgram only.
Per-agent voice/model configuration for Vaathiyar agents.
"""

import os
from typing import Optional

import requests


# ─── Per-Agent Voice & Model Configuration ─────────────────────────────────
AGENT_VOICES = {
    "supervisor": {
        "model_id": "aura-2-thalia-en",  # confident, welcoming
        "encoding": "mp3",
    },
    "teacher": {
        "model_id": "aura-2-luna-en",   # warm, nurturing
        "encoding": "mp3",
    },
    "teacher_qa": {
        "model_id": "aura-2-luna-en",
        "encoding": "mp3",
    },
    "coder": {
        "model_id": "aura-2-asteria-en",  # precise, technical
        "encoding": "mp3",
    },
    "examiner": {
        "model_id": "aura-2-thalia-en",  # calm, evaluative
        "encoding": "mp3",
    },
    "default": {
        "model_id": "aura-2-thalia-en",
        "encoding": "mp3",
    },
}


def _resolve_model_for_agent(agent: str, default_model: str) -> str:
    """
    Resolve Deepgram model from env with precedence:
    1) DEEPGRAM_TTS_MODEL_<AGENT>
    2) DEEPGRAM_TTS_MODEL
    3) hard-coded default_model
    """
    key = f"DEEPGRAM_TTS_MODEL_{agent.upper()}"
    return (
        os.getenv(key)
        or os.getenv("DEEPGRAM_TTS_MODEL")
        or default_model
    )


class TTSEngine:
    """Deepgram TTS engine with per-agent model routing."""

    _instance: Optional["TTSEngine"] = None

    def __init__(self):
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY is required in backend/.env")
        self.api_key = api_key
        self.base_url = "https://api.deepgram.com/v1/speak"
        print("OK Deepgram TTS initialized successfully")

    @classmethod
    def get_instance(cls) -> "TTSEngine":
        """Singleton accessor"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate_speech(
        self,
        text: str,
        language: str = "en",
        speaker: Optional[str] = None,
        agent: str = "default",
    ) -> bytes:
        """
        Generate MP3 speech from text via Deepgram Speak REST API.

        Args:
            text:     Text to synthesize.
            language: Reserved for compatibility (Deepgram model controls language).
            speaker:  Reserved for compatibility (ignored in Deepgram mode).
            agent:    Agent name key: 'supervisor' | 'teacher' | 'teacher_qa'
                      | 'coder' | 'examiner' | 'default'

        Returns:
            MP3 audio as bytes. Playable via browser AudioContext.decodeAudioData().
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        config = AGENT_VOICES.get(agent, AGENT_VOICES["default"])
        model_id = _resolve_model_for_agent(agent, config["model_id"])
        encoding = config.get("encoding", "mp3")

        try:
            response = requests.post(
                self.base_url,
                params={
                    "model": model_id,
                    "encoding": encoding,
                },
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"text": text},
                timeout=30,
            )
            response.raise_for_status()
            return response.content

        except Exception as e:
            raise RuntimeError(f"Deepgram TTS failed: {e}")

    def get_available_speakers(self) -> list:
        """Return Deepgram model mapping used by this app (interface compatibility)."""
        return [
            {"id": cfg["model_id"], "name": key, "category": "deepgram_model"}
            for key, cfg in AGENT_VOICES.items()
        ]


def get_tts_engine() -> TTSEngine:
    """Get the global TTS engine singleton"""
    return TTSEngine.get_instance()
