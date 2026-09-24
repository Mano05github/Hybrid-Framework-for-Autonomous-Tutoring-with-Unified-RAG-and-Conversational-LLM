"""
Shared contracts for Gemini-Live style collaboration in PBL sessions.

This module centralizes websocket event names and turn lifecycle states,
so backend and frontend can evolve around one stable protocol.
"""

from dataclasses import dataclass
from typing import Optional


# Incoming event types (client -> server)
INCOMING_EVENTS = {
    "canvas_snapshot",
    "student_message",
    "voice_context",
    "voice_start",
    "voice_end",
    "request_hint",
    "submit_solution",
    "run_code",
    "telemetry_event",
    "idle_status",
    "interrupt",
}

# Outgoing event types (server -> client)
OUTGOING_EVENTS = {
    "state_sync",
    "interim_transcript",
    "final_transcript",
    "ai_text_delta",
    "ai_voice",
    "typing_start",
    "typing_stop",
    "code_result",
    "highlight",
    "mastery_update",
    "session_end",
    "error",
}


TURN_LISTENING = "listening"
TURN_TRANSCRIBING = "transcribing"
TURN_REASONING = "reasoning"
TURN_SPEAKING = "speaking"
TURN_INTERRUPTED = "interrupted"


@dataclass
class TurnState:
    turn_id: str
    status: str = TURN_LISTENING
    interrupted: bool = False
    source: Optional[str] = None
