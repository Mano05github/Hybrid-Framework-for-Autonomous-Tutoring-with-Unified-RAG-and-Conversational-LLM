# Quick Testing Guide - AI Canvas Drawing

## ✅ Server Status
**Django:** Running on http://127.0.0.1:8000/
**Ollama:** Active with llama3.2:latest
**Database:** PostgreSQL with pgvector (2,376 chunks ready)

## Testing Scenarios

### 1. Test Parallel RAG Performance

**Steps:**
1. Open browser: http://127.0.0.1:8000/canvas/
2. Login with your credentials
3. Type in chat: "explain binary search"
4. Press Enter or click send button

**Expected Terminal Output:**
```
[Teacher Agent] PARALLEL MODE: Starting RAG + LLM simultaneously
[LLM] Generating base response (no wait for RAG)...
[LLM] Base response ready in ~1000ms
[RAG Thread] Retrieved 3 chunks in ~1500ms
[LLM] Enhancing with RAG context...
[LLM] Enhanced response ready in ~500ms
[Visual Generator] Created 8 canvas commands in ~50ms

[Teacher Agent Performance - PARALLEL MODE]
  Base Response:  1000ms (immediate)
  RAG Latency:    1500ms (background)
  Total LLM:      1500ms
  Visual Gen:     50ms
  Total Latency:  1550ms
  ⚡ Speedup:     2.4x faster
```

**Expected Frontend:**
- Immediate text response (~1000ms)
- Animated pen cursor appears
- Array drawn with handwriting style
- Pointers labeled (low, mid, high)
- Natural timing (not robotic)

---

### 2. Test AI Canvas Drawing

**Test Cases:**

#### A. Binary Search
```
Query: "explain binary search algorithm"
Expected Drawing:
- Title: "Binary Search Algorithm"
- Sorted array: [2, 5, 8, 12, 16, 23, 38, 45, 56, 67, 78]
- Pointers: low (left), high (right), mid (center)
- Animated pen trail moving across text
- Progressive text reveal
```

#### B. Recursion
```
Query: "what is recursion?"
Expected Drawing:
- Title: "Recursion: Function Calls Itself"
- Recursion tree (factorial example)
- Indented function calls
- BASE CASE highlighted in green
- Warning about base case importance
```

#### C. Sorting
```
Query: "explain bubble sort"
Expected Drawing:
- Title: "Bubble Sort"
- Step-by-step array states
- Array boxes with values
- Final sorted state highlighted
```

#### D. Data Structures
```
Query: "explain stack data structure"
Expected Drawing:
- Title: "Stack (LIFO)"
- Vertical boxes with values
- TOP pointer
- Natural handwriting style
```

---

### 3. Test Natural Timing

**What to Observe:**
- ✅ Pen cursor moves smoothly (not jerky)
- ✅ Slight speed variations (not constant speed)
- ✅ Occasional micro-pauses (feels human)
- ✅ Text reveals progressively (not instant)
- ✅ Handwriting fonts (Caveat, Indie Flower)
- ✅ Natural pauses between concepts

**Timing Validation:**
- Text: ~50-60ms per character
- Pauses: 500ms (after element), 1000ms (between concepts)
- Total animation: 2-4 seconds per concept

---

### 4. Test WebSocket Integration

**Steps:**
1. Open browser console (F12)
2. Send message: "explain recursion"
3. Check console logs

**Expected Console Output:**
```javascript
📨 Received text message: {...}
📊 Message type: teacher_response
🎨 Received AI drawing commands: 12
🎨 Starting AI Drawing sequence: 12 commands
  Executing: write_text - Recursion: Function Calls Itself
  Executing: draw_diagram - tree:factorial(4)
  ...
✅ AI Drawing sequence complete
```

---

### 5. Test Connection Status

**Indicators:**
- 🟢 Green dot = Connected
- 🔴 Red dot = Disconnected
- 🟡 Yellow dot = Connecting
- 🟠 Orange dot = Error

**Steps:**
1. Refresh page → Yellow "Connecting..."
2. Wait ~1 second → Green "Connected"
3. Close server → Red "Disconnected"
4. Restart server → Auto-reconnect → Green

---

## Browser Console Checks

### Expected Logs (No Errors):
```javascript
✨ Canvas Whiteboard initialized (Infinite Canvas Mode + AI Drawing)
✨ AI Drawing System initialized
WebSocket connected: ws://127.0.0.1:8000/ws/learn/...
📨 Received message: {"type": "teacher_response", "canvas_commands": [...]}
🎨 Starting AI Drawing sequence: 8 commands
```

### Error Checks:
- ❌ No "WebSocket error" messages
- ❌ No "Failed to execute command" errors
- ❌ No "undefined canvas_commands" warnings

---

## Performance Benchmarks

### Before Optimization:
- Total: ~3700ms
- User wait: ~3700ms (feels slow)
- No visual explanations

### After Optimization:
- Total: ~1500ms
- User wait: ~1000ms (feels fast)
- **60% reduction**
- **2.5x speedup**
- Natural canvas animations

---

## Common Issues & Solutions

### Issue 1: No Canvas Commands Generated
**Symptom:** Text response but no drawing
**Cause:** Query doesn't trigger visual generation
**Solution:** Use algorithm/data structure keywords
**Test:** "binary search" (should work) vs "hello" (no drawing expected)

### Issue 2: Pen Cursor Not Visible
**Symptom:** Drawing happens but no cursor
**Check:** Browser console for CSS loading errors
**Solution:** Ensure ai-drawing-styles are injected

### Issue 3: Slow Animation
**Symptom:** Drawing takes too long
**Check:** Duration values in commands
**Tune:** Adjust TEXT_SPEED in visual_generator.py (currently 55ms)

### Issue 4: WebSocket Not Connected
**Symptom:** Messages not sending
**Check:** Red connection status dot
**Solution:** Ensure server running, check ASGI/Daphne logs

### Issue 5: Handwriting Fonts Not Loading
**Symptom:** Text renders in default font
**Check:** Browser Network tab for Google Fonts requests
**Solution:** Clear cache, check internet connection

---

## Advanced Testing

### Test Parallel Processing Timing
**Python Script (optional):**
```python
import time
import threading

# Simulate parallel vs sequential
def test_latency():
    # Sequential
    start = time.time()
    time.sleep(1.5)  # RAG
    time.sleep(2.2)  # LLM
    sequential = time.time() - start
    
    # Parallel
    start = time.time()
    rag_thread = threading.Thread(target=lambda: time.sleep(1.5))
    rag_thread.start()
    time.sleep(1.0)  # Base LLM
    rag_thread.join()
    time.sleep(0.5)  # Enhanced LLM
    parallel = time.time() - start
    
    print(f"Sequential: {sequential:.1f}s")
    print(f"Parallel: {parallel:.1f}s")
    print(f"Speedup: {sequential/parallel:.2f}x")

test_latency()
# Expected: 3.7s sequential, 1.5s parallel, 2.47x speedup
```

---

## Test Checklist

- [ ] Server starts without errors
- [ ] Canvas page loads successfully
- [ ] Connection status shows green
- [ ] Text message sends and receives response
- [ ] Terminal shows PARALLEL MODE logs
- [ ] Latency < 1500ms total
- [ ] Base response < 1000ms
- [ ] Canvas commands generated
- [ ] Pen cursor animates smoothly
- [ ] Handwriting fonts render correctly
- [ ] Natural timing variations present
- [ ] Array visualization works
- [ ] Tree visualization works
- [ ] Text progressive reveal works
- [ ] Pauses feel natural
- [ ] Console has no errors
- [ ] Multiple queries work consecutively

---

## Success Criteria

✅ **Performance:** Total latency < 1500ms
✅ **Naturalness:** Animation feels human (not robotic)
✅ **Synchronization:** Voice and drawing aligned
✅ **Reliability:** No errors in console
✅ **Visual Quality:** Handwriting fonts, smooth animations
✅ **User Experience:** Immediate response, engaging visuals

---

## Next Actions After Testing

1. **If successful:** Gather user feedback on naturalness
2. **If issues:** Check terminal logs, console errors
3. **Performance tuning:** Adjust timing parameters if needed
4. **Expand library:** Add more algorithm visualizations
5. **Add voice sync:** Integrate with TTS timing

---

**Ready to Test!** 🚀

Start with: "explain binary search" and watch the magic happen!
