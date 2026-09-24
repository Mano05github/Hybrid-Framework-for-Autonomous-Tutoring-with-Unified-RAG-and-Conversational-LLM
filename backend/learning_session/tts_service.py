"""
ElevenLabs TTS Service — Replaces the previous MOSS TTS implementation.
Provides per-agent voice synthesis with conversation context awareness.

All agents use the same custom voice: Don738TmE7yzTZFldLcf
"""

import os
import asyncio
import logging
from typing import Optional, Dict

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

logger = logging.getLogger(__name__)

# ─── Custom voice ID (same for all agents) ─────────────────────────────────
_VOICE_ID = "Don738TmE7yzTZFldLcf"

# ─── Agent → ElevenLabs voice configuration ────────────────────────────────
AGENT_VOICE_CONFIG: Dict[str, Dict] = {
    "teacher": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_multilingual_v2",   # Highest quality for narration
        "output_format": "mp3_44100_128",
    },
    "teacher_qa": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_turbo_v2_5",
        "output_format": "mp3_44100_128",
    },
    "coder": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_turbo_v2_5",
        "output_format": "mp3_44100_128",
    },
    "examiner": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_turbo_v2_5",
        "output_format": "mp3_44100_128",
    },
    "visionary": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_turbo_v2_5",
        "output_format": "mp3_44100_128",
    },
    "empath": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_turbo_v2_5",
        "output_format": "mp3_44100_128",
    },
    "supervisor": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_turbo_v2_5",
        "output_format": "mp3_44100_128",
    },
    "default": {
        "voice_id":      _VOICE_ID,
        "model_id":      "eleven_turbo_v2_5",
        "output_format": "mp3_44100_128",
    },
}

# Voice expressiveness settings (shared across all voices)
_VOICE_SETTINGS = VoiceSettings(
    stability=0.5,
    similarity_boost=0.75,
    style=0.0,
    use_speaker_boost=True,
)


class MossTTSService:
    """
    ElevenLabs TTS Service with per-agent voice routing.

    Drop-in replacement for the previous MOSS-TTS-Realtime service.
    Maintains the same public interface so consumers.py needs no changes.
    """

    _instance: Optional["MossTTSService"] = None

    def __init__(self):
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY is not set in environment. "
                "Add it to backend/.env"
            )
        self.client = ElevenLabs(api_key=api_key)
        # Track active sessions for logging/stats (no model state needed)
        self.active_sessions: Dict[str, str] = {}   # session_id → current agent
        logger.info("✓ ElevenLabs TTS Service initialized (replaces MOSS TTS)")

    @classmethod
    def get_instance(cls) -> "MossTTSService":
        """Singleton accessor — same interface as previous MossTTSService"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _synthesize(self, text: str, agent: str) -> Optional[bytes]:
        """
        Blocking TTS call — runs in a thread pool via asyncio.to_thread().
        Returns MP3 bytes (browser decodeAudioData handles MP3 natively).
        """
        config = AGENT_VOICE_CONFIG.get(agent, AGENT_VOICE_CONFIG["default"])
        try:
            audio_stream = self.client.text_to_speech.convert(
                voice_id=config["voice_id"],
                text=text,
                model_id=config["model_id"],
                output_format=config["output_format"],
                voice_settings=_VOICE_SETTINGS,
            )
            return b"".join(audio_stream)
        except Exception as e:
            logger.error(f"[ElevenLabs TTS] Synthesis failed for agent '{agent}': {e}")
            return None

    def _stream_synthesis(self, text: str, agent: str):
        """
        Generator that yields raw audio chunks from ElevenLabs streaming API.
        Runs blocking — wrap with asyncio.to_thread for async use.
        """
        config = AGENT_VOICE_CONFIG.get(agent, AGENT_VOICE_CONFIG["default"])
        try:
            for chunk in self.client.text_to_speech.convert(
                voice_id=config["voice_id"],
                text=text,
                model_id=config["model_id"],
                output_format=config["output_format"],
                voice_settings=_VOICE_SETTINGS,
            ):
                if chunk:
                    yield chunk
        except Exception as e:
            logger.error(f"[ElevenLabs TTS] Stream synthesis failed for agent '{agent}': {e}")

    async def generate_audio(
        self,
        text: str,
        agent: str = "teacher",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,   # Kept for API compatibility
    ) -> Optional[bytes]:
        """
        Generate MP3 audio for the given text and agent.

        Args:
            text       : Text to synthesize.
            agent      : Agent key ('teacher'|'coder'|'examiner'|'visionary'|'empath'|'supervisor').
            session_id : Used for session tracking/logging only.
            user_id    : Reserved for future user-specific voice customization.

        Returns:
            MP3 audio bytes, or None on error.
        """
        if not text or not text.strip():
            return None

        # Track session
        if session_id:
            self.active_sessions[session_id] = agent

        logger.info(
            f"[ElevenLabs TTS] Generating for agent='{agent}', "
            f"len={len(text)}, session={session_id}"
        )

        # Run blocking HTTP call off the async event loop
        audio_bytes = await asyncio.to_thread(self._synthesize, text, agent)

        if audio_bytes:
            logger.info(
                f"[ElevenLabs TTS] Generated {len(audio_bytes)} bytes "
                f"for agent '{agent}'"
            )
        return audio_bytes

    def cleanup_session(self, session_id: str):
        """Release session tracking (no model state to clear)"""
        self.active_sessions.pop(session_id, None)
        logger.info(f"[ElevenLabs TTS] Cleaned up session: {session_id}")

    async def generate_audio_stream(
        self,
        text: str,
        agent: str = "teacher",
        session_id: Optional[str] = None,
        stop_event: Optional[asyncio.Event] = None,
    ):
        """
        Async generator — yields audio chunks for streaming to WebSocket.
        Stops early if stop_event is set (barge-in / user interruption).

        Usage:
            async for chunk in service.generate_audio_stream(text, agent, session_id, stop_event):
                await websocket.send(bytes_data=chunk)
        """
        if not text or not text.strip():
            return

        if session_id:
            self.active_sessions[session_id] = agent

        logger.info(
            f"[ElevenLabs TTS Stream] Starting for agent='{agent}', "
            f"len={len(text)}, session={session_id}"
        )

        # run_in_executor to consume the blocking generator
        loop = asyncio.get_event_loop()
        import concurrent.futures

        def _collect_chunks():
            return list(self._stream_synthesis(text, agent))

        # We cannot yield from a thread; collect in thread and send one-by-one.
        # For true streaming, we use a queue bridging the blocking generator
        # with the async consumer.
        queue: asyncio.Queue = asyncio.Queue()
        sentinel = object()

        def _produce():
            try:
                for chunk in self._stream_synthesis(text, agent):
                    # Put chunk synchronously; this runs in the thread pool
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, sentinel)

        future = loop.run_in_executor(None, _produce)

        while True:
            if stop_event and stop_event.is_set():
                logger.info(f"[ElevenLabs TTS Stream] Barge-in detected — stopping stream for session={session_id}")
                future.cancel()
                break

            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                # Check stop event and try again
                continue

            if item is sentinel:
                break

            yield item

    @staticmethod
    def _split_at_sentence_boundary(text: str, start_char: int) -> str:
        """
        Return the portion of `text` starting at the sentence boundary
        at or after `start_char`.  Used for TTS resume after barge-in.
        """
        import re
        if start_char <= 0:
            return text
        if start_char >= len(text):
            return ""
        tail = text[start_char:]
        # find a clean sentence start after punctuation + space
        m = re.search(r'(?<=[.!?])\s+', tail)
        if m:
            return tail[m.end():]
        return tail.lstrip()

    async def generate_audio_stream_resumable(
        self,
        text: str,
        start_char: int = 0,
        agent: str = "teacher",
        session_id: Optional[str] = None,
        stop_event: Optional[asyncio.Event] = None,
    ):
        """
        Async generator — like generate_audio_stream() but skips to the
        sentence boundary at or after `start_char`.
        Used for TTS resume after a barge-in interruption.
        """
        resume_text = self._split_at_sentence_boundary(text, start_char)
        if not resume_text:
            logger.info(f"[TTS Resumable] Nothing to resume after cursor={start_char}")
            return
        logger.info(
            f"[TTS Resumable] Resuming from char={start_char}, "
            f"remaining={len(resume_text)} chars, session={session_id}"
        )
        async for chunk in self.generate_audio_stream(
            text=resume_text,
            agent=agent,
            session_id=session_id,
            stop_event=stop_event,
        ):
            yield chunk


    def get_stats(self) -> Dict:
        """Service statistics — compatible with original MossTTSService.get_stats()"""
        return {
            "service":          "ElevenLabs",
            "active_sessions":  len(self.active_sessions),
            "available_voices": list(AGENT_VOICE_CONFIG.keys()),
            "model_default":    "eleven_turbo_v2_5",
            "model_teacher":    "eleven_multilingual_v2",
        }


# ─── Convenience function (backward compat) ────────────────────────────────
async def generate_tts(
    text: str,
    agent: str = "teacher",
    session_id: Optional[str] = None,
) -> Optional[bytes]:
    """
    Quick TTS generation helper.

    Example:
        audio = await generate_tts("Hello, welcome to the lesson!", agent="teacher")
    """
    service = MossTTSService.get_instance()
    return await service.generate_audio(text, agent, session_id)
