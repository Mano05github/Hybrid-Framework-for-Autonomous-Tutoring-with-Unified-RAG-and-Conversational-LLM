# Visionary Agent Strategy: The "Omniscient Observer"

## The Challenge
You require the AI to "see" updates across three distinct interfaces:
1.  **Quiz Page** (Structured data: Questions, Checked Options)
2.  **Code Editor** (Text data: Code, Terminal Output)
3.  **Whiteboard** (Unstructured data: Drawings, Handwriting)

**Constraint**: Must be *efficient* and *fast* enough to handle updates.

## The Problem with Pure Vision on Everything
Taking a screenshot of the Code Editor every time you type a character is a bottleneck:
-   **High Latency**: Uploading an image (even compressed) takes 500ms-2s.
-   **Accuracy Loss**: "Reading" code via OCR (Vision Model) is prone to errors (confusing `1` vs `l`, `;` vs `:`).
-   **Cost**: Continuous Vision API calls are expensive.

## The Solution: Hybrid "Dual-Sight" Strategy

We will give the Visionary Agent two types of "eyes":

### 1. "Virtual Sight" (Semantic/Data Vision)
**Best for**: Quiz UI & Code Editor.
Instead of looking at *pixels*, the AI looks at the *State*.
-   **Mechanism**: The Frontend sends lightweight JSON deltas (changes) via WebSocket.
-   **Speed**: < 50ms (Instant).
-   **Why**: The AI doesn't need to *see* the blue pixel of a selected radio button to know you selected "Option B". It just needs the data: `selected_option: 1`.

| Interface | User Action | "Virtual Sight" Data Sent | AI Perception |
| :--- | :--- | :--- | :--- |
| **Quiz** | User clicks "Option B" | `{ type: "quiz_update", q_id: 5, selected: 1 }` | "I see the user selected Option B." |
| **Code** | User types `print()` | `{ type: "code_change", content: "print()" }` | "I see the user typed a print statement." |

### 2. "True Sight" (Pixel Vision)
**Best for**: Whiteboard & Layout Issues.
For unstructured creativity, we use actual screenshots.
-   **Mechanism**: Capture Canvas as Base64 Image.
-   **Trigger**:
    -   **On Demand**: When user says "Look at this", "Check my diagram".
    -   **Smart Trigger**: When user stops drawing for 3 seconds (Debounced).
-   **Why**: A drawing of a tree cannot be easily described in JSON.

## Implementation Architecture

### A. The "snapshot" Protocol
We will define a unified state object that the Visionary Agent can access:

```python
class VisionaryState:
    # 1. Virtual Sight (Always real-time sync)
    code_context: str       # "def binary_search..."
    quiz_context: dict      # { current_q: 5, selected: 1 }
    
    # 2. True Sight (On Trigger)
    visual_snapshot: str    # Base64 Image of Whiteboard
```

### B. The "Saccade" Technique (Efficiency Trick)
Human eyes don't focus on everything at once; they "saccade" (jump) to the relevant area.
Our Agent will do the same:

1.  **IF** User asks "Is my code correct?" -> **Look at Virtual Sight (Code String)**.
2.  **IF** User asks "Is this diagram correct?" -> **Request Snapshot -> Look at True Sight (Pixels)**.
3.  **IF** User asks "Do these match?" -> **Look at Both**.

## Summary of Strategy
| Page | Technique | Speed | Accuracy |
| :--- | :--- | :--- | :--- |
| **Quiz** | **Virtual Sight** (JSON State) | Instant | 100% |
| **Code** | **Virtual Sight** (Text Stream) | Instant | 100% |
| **Whiteboard** | **True Sight** (Image Snapshot) | ~1.5s | High (Llama 3.2 Vision) |

**Recommendation**: We proceed with **Virtual Sight** for Quiz/Code (updates already flow via WebSocket) and strictly use **True Sight** (Screenshots) for the Whiteboard or if you specifically say "Look at my screen".
