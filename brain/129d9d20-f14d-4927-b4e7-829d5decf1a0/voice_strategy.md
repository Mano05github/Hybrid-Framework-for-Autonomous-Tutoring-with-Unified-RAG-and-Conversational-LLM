# Voice-First Strategy: The Vocal Loop

## The Goal
The user should **talk** to the AI, and the AI should **speak** back. The text chat is just a history log, not the controller.

## The Challenge: Latency
Real-time voice conversation requires a response in <1 second.
*   **Slow Way**: Record Audio -> Upload to Server -> Server Transcribes (Whisper) -> LLM Thinks -> Server TTS -> Download Audio -> Play. (**Total: 4-6s** - Too slow for conversation).
*   **Fast Way**: Transcribe locally -> Send Text -> LLM Thinks -> Send Text -> Speak locally. (**Total: 1-2s**).

## Proposed Architecture: "The Hybrid Loop"

### 1. The Ear (Frontend)
We will use the browser's built-in **Web Speech API** (or deepgram-browser-sdk later).
*   **Why?** Zero latency. It converts voice to text *as you speak*.
*   **Logic**:
    *   User clicks "Mic" (or "Always On").
    *   Browser handles `SpeechRecognition`.
    *   Final result is sent via WebSocket: `{"type": "chat_message", "message": "Explain this code."}`.

### 2. The Brain (Backend) - **Logic is Ready**
*   The Orchestrator processes the text exactly as it does now.
*   It context-aware Gemini logic remains the same.
*   It returns text: `{"type": "ai_response", "message": "This code creates a loop."}`.

### 3. The Mouth (Frontend)
When the frontend receives the AI response:
*   **Option A: Browser TTS (Free, Fast, Robotic)**
    *   `window.speechSynthesis.speak(...)`.
    *   Good for testing logic.
*   **Option B: ElevenLabs / OpenAI TTS (Paid, Realistic)**
    *   Frontend sends text to TTS API -> Plays audio stream.
    *   Much better "Persona" feel.

### 4. The Filter: "Smart Gating" (Solving the Cocktail Party Problem)
The user wants "Always On" but doesn't want the AI to answer when they talk to their mom.

**Strategy: Intent Classification Layer**
Before generating a full answer, the Brain performs a fast check:
1.  **Frontend VAD**: Only send text if *speech* is detected (silence is ignored).
2.  **Backend Gating**: The Orchestrator quickly asks: *"Is this input directed at me (the Tutor)?"*
    *   *Input*: "Can you explain that again?" -> **YES** -> Respond.
    *   *Input*: "Pass me the salt." -> **NO** -> Ignore.
    *   *Input*: "Turn up the volume." -> **COMMAND** -> Execute Command.

**Implementation**:
We prepend a "System Instruction" to the Gemini call:
*"If the user's input is clearly off-topic or background conversation, respond with [IGNORE]."*

## Implementation Plan

1.  **Refactor `VoiceAgentWidget.tsx`**:
    *   Integrate `react-speech-recognition` or native API.
    *   Visualizer should pulse *while* you speak (using `AnalyserNode`).
2.  **Auto-Send Logic**:
    *   Silence detection: When user stops speaking for 1s, auto-send the text.
3.  **Auto-Speak Logic**:
    *   When `ai_response` arrives, immediately trigger TTS.
    *   Visualizer pulses *while* AI speaks.

## Recommendation
We start with **Browser Native APIs** (Option A) to prove the cycle works instantly. Then we upgrade to **ElevenLabs** (Option B) for the "Premium" voice quality.
