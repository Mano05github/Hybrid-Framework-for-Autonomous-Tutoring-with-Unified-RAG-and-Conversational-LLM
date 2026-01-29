# Phase 8: The Adaptive Coach - Strategy & Methodology

## 1. Core Philosophy: The "Meta-Cognitive" Loop
The Adaptive Coach is not just another agent; it is the **Strategic Brain** of the system. It moves the specific interaction from *Reactive* (answering questions) to *Proactive* (optimization of learning).

### The Feedback Loop
1.  **Experience**: Student interacts (Chat, Quiz, Code, Diagram).
2.  **Observation**: The **Analyst** records raw data (time taken, errors, emotion).
3.  **Inference**: The Analyst updates the **Student Model** (Skill Levels, Learning Style).
4.  **Strategy**: The **Coach** selects the next best action (Explain, Quiz, or Console).
5.  **Action**: The **Supervisor** executes the strategy via a specialized agent.

---

## 2. Theoretical Frameworks & Algorithms

We will implement a hybrid approach combining three powerful educational data mining techniques:

### A. Bayseian Knowledge Tracing (BKT)
*   **Purpose**: To estimate the probability that a student has mastered a specific concept (e.g., "Recursion") at any given time step.
*   **Mechanism**:
    *   $P(L_t)$: Probability knowledge is learned at time $t$.
    *   $P(G)$: Probability of guessing correctly (Guess).
    *   $P(S)$: Probability of slipping (knowing but failing).
    *   $P(T)$: Probability of learning (Transition).
*   **Implementation**: A lightweight probabilistic model updated after every interaction.

### B. Item Response Theory (IRT)
*   **Purpose**: To match student ability ($\theta$) with problem difficulty ($\beta$).
*   **Mechanism**:
    *   Adaptive Selection: We pick questions where $P(Correct|\theta) \approx 0.75$ (Zone of Proximal Development).
    *   If student answers correct -> Increase $\theta$.
    *   If student fails -> Decrease $\theta$.
*   **Simplification**: We will use a modified Elo Rating System (like Chess) for dynamic difficulty adjustment.

### C. Zone of Proximal Development (ZPD)
*   **Strategy**: The system categorizes content into three zones:
    1.  **Comfort Zone**: Easy tasks for confidence boosting (Review).
    2.  **Growth Zone (ZPD)**: Conceptual challenges with scaffolding (New Learning).
    3.  **Panic Zone**: Too hard, causes frustration (Avoid).
*   **Emotion Modulation**: We weight ZPD with Emotion.
    *   *Frustrated* -> Shift towards Comfort Zone.
    *   *Bored* -> Shift towards upper ZPD.

---

## 3. Data Architecture (The Memory)

To support these algorithms, we need a robust schema in PostgreSQL (`pgvector` support is a plus for semantic similarity).

### A. `StudentProfile` Table
*   `learning_style`: (Visual, Auditory, Kinesthetic) - Inferred from agent preference.
*   `elo_rating`: Global ability score.
*   `context_vector`: Embedding of recent history.

### B. `ConceptNode` Table (The Knowledge Graph)
*   `name`: "Binary Search".
*   `difficulty`: 0.0 to 1.0.
*   `prerequisites`: FK to other ConceptNodes (Dependency Graph).

### C. `MasteryState` Table (The BKT Model)
*   `student_id`: FK.
*   `concept_id`: FK.
*   `mastery_probability`: 0.0 to 1.0.
*   `last_practiced`: Timestamp (for Spaced Repetition).
*   `forgetting_curve`: Coefficient (how fast they forget this topic).

---

## 4. The Agent Architecture

### The Analyst (The Observer)
*   **Trigger**: Post-turn (async).
*   **Input**: `SessionLog` (User Msg, AI Msg, Tool Usage).
*   **Task**:
    1.  Did the user understand? (Yes/No/Partial).
    2.  Update `MasteryState` using BKT update rule.
    3.  Update `Sentiment` trend.

### The Coach (The Strategist)
*   **Trigger**: Pre-turn (before Supervisor logic).
*   **Input**: `MasteryState`, `StudentProfile`, `CurrentIntent`.
*   **Output**: `InstructionalDirective`.
*   **Example Directives**:
    *   `SCAFFOLD`: "User is struggling. Break down the problem."
    *   `CHALLENGE`: "User is bored. Give a hard coding challenge."
    *   `PIVOT`: "User is stuck. Switch from Abstraction to Analogy."

---

## 5. Machine Learning Techniques (Phase 8b)

While Phase 8a uses logic/probabilistic models (BKT/IRT), Phase 8b allows for Deep Learning:

*   **DKT (Deep Knowledge Tracing)**: Using LSTM/Transformers to predict the next response based on the entire sequence of past interactions.
*   **RL (Reinforcement Learning)**: (Long-term goal) Treat the Tutor as an RL Agent where Reward = Student Learning Gain. We will effectively "A/B Test" teaching strategies automatically.

---

## 🗓️ Implementation Plan

1.  **Database**: Define Models (`StudentProfile`, `ConceptNode`, `MasteryState`).
2.  **Analyst**: Implement `update_mastery()` logic (BKT).
3.  **Knowledge Graph**: Seed database with ~50 CS Concepts (Algorithms, Data Structures).
4.  **Coach**: Implement `select_strategy()` logic (ZPD logic).
5.  **Integration**: Update `Supervisor` to verify with Coach before routing.
