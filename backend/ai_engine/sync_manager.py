"""
Synchronization Manager
Coordinates voice narration (TTS) with canvas drawing animations using chunk-based
acknowledgment protocol to prevent drift and enable student-paced learning.

Research-backed approach:
- Chunk duration: 2-4 seconds (cognitive processing window)
- Sync accuracy: <50ms (human perception threshold: ~100ms)
- Acknowledgment-based: Wait for "chunk complete" before proceeding
"""

import time
import asyncio
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
import json


@dataclass
class SyncChunk:
    """Single synchronized audio + visual chunk"""
    chunk_id: int
    audio_data: Optional[bytes] = None  # MP3 audio bytes
    audio_duration: float = 0.0  # Seconds
    canvas_commands: List[Dict] = field(default_factory=list)
    text_content: str = ""  # Text being spoken
    start_time: Optional[float] = None  # Playback start timestamp
    acknowledged: bool = False
    

@dataclass
class SyncSession:
    """Complete synchronization session state"""
    session_id: str
    chunks: List[SyncChunk] = field(default_factory=list)
    current_chunk_idx: int = 0
    total_duration: float = 0.0
    paused: bool = False
    speed_multiplier: float = 1.0  # Pacing mode (0.85x slow, 1.0x normal, 1.3x fast)
    created_at: float = field(default_factory=time.time)


class SynchronizationManager:
    """
    Manages voice-visual synchronization with chunk-based streaming.
    
    Key Features:
    - Acknowledgment protocol: Zero drift accumulation
    - Student-paced: Natural pause points for interruptions
    - Network resilient: Buffering handles latency
    - Adaptive pacing: Emotion-responsive speed control
    """
    
    # Default configuration
    DEFAULT_CHUNK_DURATION = 3.0  # seconds (2-4 sec optimal range)
    MAX_CHUNK_DURATION = 6.0  # seconds (cognitive limit)
    SYNC_ACCURACY_TARGET = 0.050  # 50ms
    PREFETCH_CHUNKS = 1  # Number of chunks to prefetch
    
    def __init__(self):
        self.active_sessions: Dict[str, SyncSession] = {}
        self.chunk_callbacks: Dict[str, Callable] = {}
        
    def create_session(self, session_id: str, speed_multiplier: float = 1.0) -> SyncSession:
        """
        Create a new synchronization session.
        
        Args:
            session_id: Unique identifier for this learning session
            speed_multiplier: Pacing mode (0.85=slow, 1.0=normal, 1.3=fast)
        """
        session = SyncSession(
            session_id=session_id,
            speed_multiplier=speed_multiplier
        )
        self.active_sessions[session_id] = session
        return session
    
    def add_chunk(self, session_id: str, audio_data: Optional[bytes], 
                  audio_duration: float, canvas_commands: List[Dict], 
                  text_content: str) -> SyncChunk:
        """
        Add a synchronized chunk to the session.
        
        Args:
            session_id: Session identifier
            audio_data: MP3 audio bytes (None for text-only)
            audio_duration: Duration in seconds
            canvas_commands: List of canvas drawing commands
            text_content: Text being spoken
            
        Returns:
            Created SyncChunk
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Apply speed multiplier to durations
        adjusted_duration = audio_duration / session.speed_multiplier
        
        # Adjust canvas command durations
        adjusted_commands = []
        for cmd in canvas_commands:
            cmd_copy = cmd.copy()
            if 'duration' in cmd_copy:
                cmd_copy['duration'] = int(cmd_copy['duration'] / session.speed_multiplier)
            if 'pause_after' in cmd_copy:
                cmd_copy['pause_after'] = int(cmd_copy['pause_after'] / session.speed_multiplier)
            adjusted_commands.append(cmd_copy)
        
        chunk = SyncChunk(
            chunk_id=len(session.chunks),
            audio_data=audio_data,
            audio_duration=adjusted_duration,
            canvas_commands=adjusted_commands,
            text_content=text_content
        )
        
        session.chunks.append(chunk)
        session.total_duration += adjusted_duration
        
        return chunk
    
    def get_next_chunk(self, session_id: str) -> Optional[Dict]:
        """
        Get the next chunk to play (acknowledgment-based streaming).
        
        Returns:
            Chunk data dict or None if session complete
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        if session.current_chunk_idx >= len(session.chunks):
            return None  # Session complete
        
        chunk = session.chunks[session.current_chunk_idx]
        chunk.start_time = time.time()
        
        # Prepare chunk data for frontend
        chunk_data = {
            'chunk_id': chunk.chunk_id,
            'audio_data': chunk.audio_data,  # Will be base64 encoded by websocket
            'audio_duration': chunk.audio_duration,
            'canvas_commands': chunk.canvas_commands,
            'text_content': chunk.text_content,
            'is_final': session.current_chunk_idx == len(session.chunks) - 1,
            'total_chunks': len(session.chunks),
            'speed_multiplier': session.speed_multiplier
        }
        
        return chunk_data
    
    def acknowledge_chunk(self, session_id: str, chunk_id: int) -> bool:
        """
        Acknowledge chunk completion (move to next chunk).
        
        Args:
            session_id: Session identifier
            chunk_id: Chunk ID that completed
            
        Returns:
            True if acknowledged successfully, False if session not found
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        if chunk_id < len(session.chunks):
            chunk = session.chunks[chunk_id]
            chunk.acknowledged = True
            
            # Move to next chunk
            if session.current_chunk_idx == chunk_id:
                session.current_chunk_idx += 1
            
            return True
        
        return False
    
    def pause_session(self, session_id: str):
        """Pause the current session"""
        session = self.active_sessions.get(session_id)
        if session:
            session.paused = True
    
    def resume_session(self, session_id: str):
        """Resume a paused session"""
        session = self.active_sessions.get(session_id)
        if session:
            session.paused = False
    
    def adjust_speed(self, session_id: str, speed_multiplier: float):
        """
        Adjust playback speed (adaptive pacing).
        
        Args:
            speed_multiplier: 0.85 (slow), 1.0 (normal), 1.3 (fast)
        """
        session = self.active_sessions.get(session_id)
        if session:
            # Clamp to valid range
            speed_multiplier = max(0.5, min(2.0, speed_multiplier))
            session.speed_multiplier = speed_multiplier
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get current session status"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            'session_id': session_id,
            'current_chunk': session.current_chunk_idx,
            'total_chunks': len(session.chunks),
            'progress': session.current_chunk_idx / len(session.chunks) if session.chunks else 0,
            'paused': session.paused,
            'speed_multiplier': session.speed_multiplier,
            'total_duration': session.total_duration
        }
    
    def cleanup_session(self, session_id: str):
        """Remove completed/abandoned session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.chunk_callbacks:
            del self.chunk_callbacks[session_id]
    
    def split_content_into_chunks(self, full_text: str, max_chunk_duration: Optional[float] = None) -> List[str]:
        """
        Split long text content into natural chunks (2-4 seconds each).
        
        Strategy:
        - Split at sentence boundaries (. ! ?)
        - Respect pause points (after key concepts)
        - Target 2-4 second duration (300-600 chars at ~150 WPM)
        
        Args:
            full_text: Complete text content
            max_chunk_duration: Max chunk duration in seconds (default: 4.0)
            
        Returns:
            List of text chunks
        """
        if not full_text:
            return []
        
        max_duration = max_chunk_duration or self.DEFAULT_CHUNK_DURATION
        
        # Approximate words per second (150 WPM = 2.5 words/sec)
        words_per_second = 2.5
        max_words = int(max_duration * words_per_second)
        
        # Split into sentences
        sentences = []
        current_sentence = ""
        
        for char in full_text:
            current_sentence += char
            if char in '.!?' and len(current_sentence) > 10:
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Group sentences into chunks
        chunks = []
        current_chunk = ""
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if current_word_count + sentence_words > max_words and current_chunk:
                # Flush current chunk
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_word_count = sentence_words
            else:
                current_chunk += " " + sentence
                current_word_count += sentence_words
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def estimate_audio_duration(self, text: str) -> float:
        """
        Estimate audio duration based on text length.
        
        Uses 150 WPM speaking rate (standard TTS speed).
        
        Args:
            text: Text content
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        words_per_second = 2.5  # 150 WPM
        return word_count / words_per_second


# Global singleton instance
_sync_manager = None

def get_sync_manager() -> SynchronizationManager:
    """Get the global synchronization manager instance"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SynchronizationManager()
    return _sync_manager
