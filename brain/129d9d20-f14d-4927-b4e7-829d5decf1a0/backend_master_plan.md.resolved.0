# The Master Backend Plan: Intelligent Tutoring System (ITS)

## 1. Sentiment Analysis Engine
**Goal**: Understand *how* the user feels, not just what they say.
**Strategy**: Hybrid Approach.
*   **Layer 1: Fast & Local (VADER/TextBlob)**
    *   *Real-time check* on every message.
    *   Detects "Frustration" (Negative Polarity) vs "Confidence" (Positive Polarity).
    *   *Why?* Instant feedback loop (Lat: <10ms).
*   **Layer 2: Deep Context (Gemini)**
    *   When VADER detects high negative emotion, trigger a deeper analysis via Gemini.
    *   *Prompt*: "The user seems frustrated. Analyze their last 3 messages. Is it confusion with the concept or the interface?"

**Algorithm**:
```python
if sentiment_score < -0.5:
    trigger_intervention(mode="encouragement")
    simplify_explanation_level()
```

## 2. Adaptive Feedback Loop (The Core)
**Goal**: Adjust the difficulty based on user performance.
**Technique**: **Knowledge Tracing (Simplified BKT)**.

### The "User Model"
We maintain a state vector for each topic:
```json
{
  "topic": "Binary Search Trees",
  "mastery_score": 0.4,  // 0.0 to 1.0
  "frustration_index": 0.1,
  "preferred_learning_style": "visual" // inferred from questions
}
```

### The Loop Logic
1.  **Input**: User code execution result (Pass/Fail) + Voice Sentiment.
2.  **Update**:
    *   *If Code Pass*: Increase `mastery_score` (+0.1).
    *   *If Code Fail*: Decrease `mastery_score` (-0.05). Increase `frustration_index`.
3.  **Adaptation**:
    *   *High Mastery*: "Challenge Mode" (Less hints, harder questions).
    *   *High Frustration*: "Support Mode" (More hints, encouraging tone, break down tasks).

## 3. Dynamic Content Adaptation
**Goal**: Serve the right content at the right time.
**Strategy**: **Difficulty-Tiered RAG**.

### Content Architecture
Tag all RAG chunks (PDFs/Docs) with a metadata tag: `difficulty` (Beginner, Intermediate, Advanced).

### The Retrieval Algorithm
When fetching context for the AI:
*   *If Mastery < 0.3*: Filter RAG for `difficulty="Beginner"`.
*   *If Mastery > 0.8*: Filter RAG for `difficulty="Advanced"`.

**Result**: A beginner never sees complex "Red-Black Tree Optimization" content until they master standard BSTs.

## 4. Implementation Phase Roadmap
1.  **Phase A: Sentiment** -> Install `nltk`/`textblob`. Add `analyze_sentiment()` middleware in Orchestrator.
2.  **Phase B: User Model** -> Create `UserProgress` DB model. Track `mastery_score`.
3.  **Phase C: Adaptation** -> Wire the "User Model" into the AI Prompt (`You are talking to a Beginner. Keep it simple.`).
