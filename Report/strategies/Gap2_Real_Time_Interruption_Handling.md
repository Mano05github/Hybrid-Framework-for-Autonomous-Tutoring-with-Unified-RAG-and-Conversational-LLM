# Gap 2: Real-Time Interruption Handling Strategy

## Overview

Gap 2 addresses the challenge of handling user interruptions during agent responses, enabling natural conversational flow where students can ask clarifying questions, correct misunderstandings, or redirect the conversation without waiting for the current response to complete.

## Problem Statement

Traditional chatbot systems operate on a strict turn-based model: the system speaks, then waits for user input. This creates unnatural interactions where:
- Students must wait for lengthy explanations to finish before asking questions
- Misunderstandings compound as incorrect information continues to be delivered
- Engagement decreases when students cannot interject naturally
- Time is wasted on irrelevant tangents that could be immediately corrected

## Solution Architecture

### Dual-Channel Communication

**WebSocket Duplex Stream:**
```typescript
interface WebSocketChannels {
  outputStream: ReadableStream<AgentMessage>;  // Agent → User
  inputStream: WritableStream<UserInput>;      // User → Agent
  controlChannel: EventEmitter;                // Interruption signals
}
```

**Interruption Flow:**
```
User speaks/types during agent response
  ↓
Frontend detects input activity
  ↓
Send INTERRUPT signal via control channel
  ↓
Backend pauses current agent execution
  ↓
Buffer partial response for context
  ↓
Process new user input
  ↓
Generate new response with continuation context
  ↓
Resume or replace original response
```

### Voice Activity Detection (VAD)

**Real-Time Detection:**
```python
import webrtcvad

class VADInterruptDetector:
    def __init__(self, aggressiveness=3):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.speaking = False
        
    def is_interruption(self, audio_frame, sample_rate=16000):
        """
        Detect if user is speaking while agent is responding
        
        Returns:
            True if user speech detected during agent output
        """
        is_speech = self.vad.is_speech(audio_frame, sample_rate)
        
        # Check if agent is currently speaking
        if self.agent_speaking and is_speech:
            # Verify sustained speech (>300ms)
            if self.sustained_speech_duration() > 0.3:
                return True
        
        return False
```

### Interruption Types

**1. Clarification Interrupt**
```
Agent: "The binary search algorithm works by dividing the array..."
User: "Wait, does the array need to be sorted first?"
System: [Pauses, saves context]
        "Yes, excellent question! Binary search requires..."
```

**2. Correction Interrupt**
```
Agent: "Next, we iterate through the linked list..."
User: "Actually, I wanted to know about arrays, not linked lists"
System: [Stops, context switch]
        "My apologies, let's talk about arrays instead..."
```

**3. Tangent Interrupt**
```
Agent: "The time complexity of merge sort is O(n log n)..."
User: "Can you give me an example first?"
System: [Pauses, reorders explanation]
        "Of course! Let me show you a concrete example..."
```

**4. Emergency Stop**
```
Agent: [Giving long explanation]
User: "Stop" or "Never mind"
System: [Immediate termination]
        "Okay, what would you like to know instead?"
```

## Implementation Details

### Frontend Interruption Detection

```typescript
class InterruptionHandler {
  private isAgentSpeaking: boolean = false;
  private userInputBuffer: string = '';
  private interruptThreshold: number = 300; // ms
  private lastInputTime: number = 0;
  
  detectInterruption(inputEvent: InputEvent): boolean {
    const now = Date.now();
    const timeSinceLastInput = now - this.lastInputTime;
    
    // User is actively typing/speaking
    if (timeSinceLastInput < this.interruptThreshold) {
      if (this.isAgentSpeaking) {
        this.sendInterruptSignal();
        return true;
      }
    }
    
    this.lastInputTime = now;
    return false;
  }
  
  sendInterruptSignal() {
    this.websocket.send(JSON.stringify({
      type: 'INTERRUPT',
      timestamp: Date.now(),
      partial_input: this.userInputBuffer
    }));
  }
}
```

### Backend Interruption Processing

```python
class InterruptionManager:
    def __init__(self):
        self.current_response_generator = None
        self.interruption_buffer = []
        self.context_stack = []
        
    async def handle_interrupt(self, user_message: str, session_id: str):
        """
        Process user interruption during agent response
        """
        # 1. Stop current generation
        if self.current_response_generator:
            self.current_response_generator.cancel()
            
            # Save partial response for context
            partial_response = await self.get_partial_response()
            self.context_stack.append({
                'partial_response': partial_response,
                'interrupted_at': time.time(),
                'original_query': self.current_query
            })
        
        # 2. Classify interruption type
        interrupt_type = await self.classify_interrupt(user_message)
        
        # 3. Route to appropriate handler
        if interrupt_type == 'CLARIFICATION':
            return await self.handle_clarification(user_message)
        elif interrupt_type == 'CORRECTION':
            return await self.handle_correction(user_message)
        elif interrupt_type == 'STOP':
            return await self.handle_emergency_stop()
        else:
            return await self.handle_new_query(user_message)
    
    async def classify_interrupt(self, message: str) -> str:
        """
        Use NLU to classify interruption intent
        """
        keywords = {
            'CLARIFICATION': ['what', 'why', 'how', 'explain', 'mean'],
            'CORRECTION': ['no', 'not', 'wrong', 'actually', 'instead'],
            'STOP': ['stop', 'wait', 'never mind', 'cancel', 'enough']
        }
        
        message_lower = message.lower()
        
        for intent, words in keywords.items():
            if any(word in message_lower for word in words):
                return intent
        
        return 'NEW_QUERY'
```

### Context Preservation

**Dialogue State with Interruptions:**
```json
{
  "session_id": "sess_123",
  "current_topic": "binary_search",
  "dialogue_history": [
    {
      "turn": 1,
      "user": "Explain binary search",
      "agent": "Binary search is an efficient algorithm...",
      "status": "completed"
    },
    {
      "turn": 2,
      "user": "How does it work?",
      "agent": "It works by dividing the array in half...",
      "status": "interrupted",
      "interrupted_at_word": 12,
      "partial_response": "It works by dividing the array in half and comparing the middle element"
    },
    {
      "turn": 3,
      "user": "Wait, does the array need to be sorted?",
      "agent": "Yes, excellent question! Binary search requires a sorted array...",
      "status": "completed",
      "continuation_context": true
    }
  ],
  "interruption_count": 1
}
```

### Streaming Response with Checkpoints

```python
async def generate_streaming_response(
    agent: Agent,
    query: str,
    session_id: str
):
    """
    Generate response with interruption checkpoints
    """
    response_chunks = []
    checkpoint_interval = 50  # words
    
    async for chunk in agent.generate_response(query):
        # Check for interruption signal
        if await check_interrupt_signal(session_id):
            # Save checkpoint
            await save_response_checkpoint(
                session_id=session_id,
                partial_response=' '.join(response_chunks),
                position=len(response_chunks)
            )
            raise InterruptedException()
        
        response_chunks.append(chunk)
        
        # Send chunk to client
        await send_chunk(session_id, chunk)
        
        # Periodic checkpoints
        if len(response_chunks) % checkpoint_interval == 0:
            await save_response_checkpoint(
                session_id=session_id,
                partial_response=' '.join(response_chunks),
                position=len(response_chunks)
            )
    
    return ' '.join(response_chunks)
```

## Integration with Other Components

### With Supervisor Agent

```python
class SupervisorWithInterrupts(SupervisorAgent):
    def handle_message(self, message: str, session_id: str):
        # Check if this is an interrupt
        if self.is_interruption(session_id):
            return self.interrupt_manager.handle_interrupt(
                message, session_id
            )
        
        # Normal processing
        return super().handle_message(message, session_id)
    
    def is_interruption(self, session_id: str) -> bool:
        session = self.session_manager.get_session(session_id)
        return session.agent_is_responding and not session.response_complete
```

### With Voice Assistant (Gap 1)

```python
class VoiceInterruptHandler:
    def __init__(self):
        self.vad = webrtcvad.Vad(mode=3)
        self.tts_playing = False
        
    async def monitor_interruptions(self):
        """
        Monitor microphone input while TTS is playing
        """
        while True:
            if self.tts_playing:
                audio_frame = await self.capture_audio_frame()
                
                if self.vad.is_speech(audio_frame, 16000):
                    # Sustained speech detected
                    if await self.confirm_user_speech(duration=0.5):
                        # Stop TTS playback
                        await self.stop_tts()
                        
                        # Start STT for new input
                        user_input = await self.capture_user_speech()
                        
                        # Send interruption
                        await self.send_interrupt(user_input)
```

## Performance Characteristics

| Metric | Target | Implementation |
|--------|--------|----------------|
| Interrupt detection latency | <100ms | VAD + buffer monitoring |
| Response cancellation time | <50ms | Generator cancellation |
| Context preservation accuracy | >95% | Checkpointing system |
| False positive interrupts | <5% | VAD threshold tuning |
| Resume capability | Yes | Context stack with continuation |

## Edge Cases and Handling

### 1. Rapid Multiple Interruptions
**Scenario**: User interrupts, then immediately interrupts again

**Solution**: Queue interruptions, process sequentially with timeout
```python
class InterruptionQueue:
    def __init__(self, max_queue_size=3):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.processing = False
        
    async def add_interrupt(self, message: str):
        if self.queue.full():
            # Drop oldest interrupt
            await self.queue.get()
        await self.queue.put(message)
        
        if not self.processing:
            await self.process_queue()
```

### 2. Ambiguous Interruption Intent
**Scenario**: Unclear if user wants clarification or topic change

**Solution**: Ask for confirmation
```
User: "Wait, what about..." [interrupts]
System: "Would you like me to:
         1. Clarify the current topic
         2. Move to a different topic
         3. Continue where I left off"
```

### 3. Network Latency Issues
**Scenario**: Interrupt signal delayed due to network

**Solution**: Client-side prediction + server reconciliation
```typescript
class LatencyCompensation {
  predictInterrupt() {
    // Client immediately shows "Processing..." state
    this.showProcessingState();
    
    // Send interrupt with timestamp
    this.sendInterrupt({
      timestamp: Date.now(),
      client_state: 'INTERRUPT_PREDICTED'
    });
  }
  
  reconcile(serverResponse) {
    // If prediction was wrong, revert
    if (serverResponse.was_false_positive) {
      this.revertProcessingState();
    }
  }
}
```

## Testing Strategy

### Unit Tests
```python
def test_interruption_detection():
    handler = InterruptionHandler()
    
    # Test during agent response
    handler.set_agent_speaking(True)
    user_input = "wait, what?"
    assert handler.is_interruption(user_input) == True
    
    # Test when agent not speaking
    handler.set_agent_speaking(False)
    assert handler.is_interruption(user_input) == False

def test_context_preservation():
    manager = InterruptionManager()
    
    # Start response
    manager.start_response("Explain merge sort", "session_1")
    
    # Interrupt mid-response
    manager.interrupt("Wait, what's a sorted array?")
    
    # Verify context saved
    context = manager.get_context("session_1")
    assert context['partial_response'] is not None
    assert context['original_query'] == "Explain merge sort"
```

### Integration Tests
```python
async def test_end_to_end_interruption():
    # Start learning session
    session = await create_session()
    
    # Send query
    response_stream = await session.ask("Explain binary search")
    
    # Receive partial response
    chunks = []
    async for chunk in response_stream:
        chunks.append(chunk)
        
        # Interrupt after 5 chunks
        if len(chunks) == 5:
            await session.interrupt("Wait, does it need to be sorted?")
            break
    
    # Verify new response
    new_response = await session.get_latest_response()
    assert "sorted" in new_response.lower()
    assert new_response != ' '.join(chunks)
```

## Current Implementation Status

- ✅ WebSocket duplex communication
- ✅ Frontend input monitoring
- ✅ Backend interrupt signal handling
- ⏳ VAD-based voice interruption detection
- ⏳ Context preservation and checkpointing
- ⏳ Interruption classification (NLU-based)
- ⏳ Resume/continuation logic
- ⏳ Integration with streaming LLM responses

## Dependencies

- **Frontend**: WebSocket API, MediaRecorder API
- **Backend**: Django Channels, asyncio, webrtcvad
- **Models**: NLU model for intent classification (already in use)

## Future Enhancements

1. **Predictive Interruption**: Anticipate likely interruptions based on student history
2. **Interruption Analytics**: Track interruption patterns to improve explanations
3. **Smart Resume**: Auto-resume after clarification if student gives no new input
4. **Multi-Modal Interruptions**: Gesture-based interrupts via webcam
5. **Collaborative Interrupts**: In multi-student sessions, handle interruptions from multiple sources

## Conclusion

Gap 2 transforms the tutoring experience from rigid turn-taking to natural, flowing conversation. By enabling interruptions, students can engage more actively with the learning material, immediately addressing confusion or redirecting ineffective explanations. This creates a more human-like tutoring interaction that respects student agency and adapts to their real-time needs.

**Current Implementation Status**: 50% complete (WebSocket infrastructure ready, voice interruption pending)
**Estimated Completion**: 2-3 weeks (pending voice assistant integration from Gap 1)
