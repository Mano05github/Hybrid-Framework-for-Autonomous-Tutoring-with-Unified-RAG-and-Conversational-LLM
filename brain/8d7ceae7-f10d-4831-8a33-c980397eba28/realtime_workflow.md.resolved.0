# Realtime Interaction Workflow (The "Pulse" Engine)

To achieve the fluid, life-like interaction seen in the GPT-4o demo, our system must operate on a **millisecond-level event loop**.

## 1. The Interaction States
The interface has 4 distinct states, governed by the "4 Dots" component.

| State | Trigger | UI Behavior | Backend Action |
| :--- | :--- | :--- | :--- |
| **Idle** | No input > 3s | Dots breathe gently (Scale 1.0 -> 1.1) | WebSocket open, Heartbeat |
| **Listening** | User Speech (VAD) | Dots pulse with **Mic Amplitude** | Stream Audio Chunks -> STT Service |
| **Thinking** | Speech End Detected | Dots spin / color shift | LLM Generation (Context + RAG) |
| **Speaking** | AI Response Ready | Dots pulse with **Output Amplitude** | Stream TTS Audio + **Canvas Commands** |

## 2. The Data Flow (The "Sync")

This is the critical part. Audio and Visuals must happen *together*.

### A. Input (User Speaks)
1.  **Browser**: Web Audio API detects sound.
2.  **Client**: Emits `audio_stream` events via WebSocket.
3.  **UI**: Updates "4 Dots" height based on local volume (Instant feedback, 0ms latency).

### B. Processing (The Brain)
1.  **Server**: Accumulates audio -> Transcribes (Whisper).
2.  **Server**: Feeds text to LLM (with System Prompt: "You are a Socratic Tutor...").
3.  **LLM**: Generates a response stream.
    *   *Text Token*: "The hypotenuse..."
    *   *Action Token*: `[DRAW_LINE: A->B]`

### C. Output (The Response)
The server sends a **multimodal packet**:
```json
{
  "audio_chunk": "<base64_mp3>",
  "text_segment": "The hypotenuse is strictly opposite...",
  "canvas_action": {
    "tool": "highlighter",
    "coordinates": [100, 200, 300, 400],
    "color": "yellow"
  }
}
```

### D. Client Execution (The Magic)
1.  **Audio Player**: Queues the `audio_chunk`.
2.  **Event Bus**: Listens for the *exact moment* that audio chunk starts playing.
3.  **Canvas**: **Executes `canvas_action` instantly** when the audio starts.
    *   *Result*: The AI says "This line here" AND the line turns yellow at the exact same time.

## 3. Technology Stack
-   **Frontend**: Next.js + `react-konva` (Canvas) + Web Audio API.
-   **Transport**: `Socket.io` or Native WebSockets (for bi-directional streaming).
-   **Backend**: Python (Django/FastAPI) to handle the async event loop.

## 4. Latency Goals
-   **Voice-to-Dots**: `0ms` (Client-side physics).
-   **Voice-to-Answer**: `< 1500ms` (Optimized LLM inference).
