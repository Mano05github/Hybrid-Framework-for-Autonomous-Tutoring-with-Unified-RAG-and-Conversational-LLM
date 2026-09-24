# Adaptive Personal AI Tutor System

### Architecture & Teaching Engine Blueprint

*For 8th--12th Grade Personalized Learning Platform*

------------------------------------------------------------------------

# 1. Vision

Build a **Personal AI Tutor** that:

-   Remembers student performance across grades
-   Adapts difficulty dynamically
-   Detects learning style automatically
-   Recommends next topics intelligently
-   Allows student free exploration without conflict
-   Includes emotional tone adaptation
-   Conducts structured sessions with mini-tests
-   Tracks mastery persistently

------------------------------------------------------------------------

# 2. High-Level Learning Funnel

``` mermaid
flowchart TD
    A[Dashboard] --> B[Learn Page]
    B --> C[Subject Hub]
    C --> D[Topic Page]
    D --> E[Voice Supervisor Session]
    E --> F[Mini Test]
    F --> G[Update Student Profile]
    G --> H[Generate Recommendations]
    H --> B
```

## Page Responsibilities

### Dashboard

-   Analytics overview
-   Performance tracking
-   Streaks and summary

### Learn Page

-   Displays all subjects (Maths, Physics, etc.)
-   Global academic progress
-   AI recommendations

### Subject Hub

-   Shows subject-level overview
-   Subject progress bar
-   Quick stats and filters

### Topic Page (New Explicit Layer)

-   Lists all topics/concepts under selected subject
-   Displays topic mastery status
-   Shows difficulty level
-   Allows student to choose specific topic
-   Highlights AI-recommended topic
-   Checks prerequisites before session start

### Voice Supervisor Session

-   Adaptive Hybrid Teaching Model
-   Dynamic difficulty adjustment
-   Socratic mistake handling
-   Voice interruption support

------------------------------------------------------------------------

# 3. Teaching Model: Adaptive Hybrid System

The session follows 5 structured phases:

1.  Diagnostic Warmup
2.  Structured Explanation
3.  Guided Practice
4.  Adaptive Difficulty Adjustment
5.  Mini Test + Reflection

------------------------------------------------------------------------

# 4. Session Flow Architecture

``` mermaid
flowchart TD
    A[Session Start] --> B[Load Student Profile]
    B --> C[Check Topic Mastery]
    C --> D[Set Initial Difficulty]
    D --> E[Diagnostic Questions]
    E --> F[Adaptive Learning Loop]
    F --> G[Mini Test]
    G --> H[Update Mastery + Learning Style]
    H --> I[Generate Next Topic Recommendation]
```

------------------------------------------------------------------------

# 5. Adaptive Difficulty Logic

If 2 consecutive wrong answers: → Drop difficulty by 1 level

If student fails 3 times at lower level: → Trigger Concept Reinforcement
Mode - Short explanation - One visual example - One guided question

If correct after reinforcement: → Return to normal difficulty Else: →
Break topic into sub-concept

------------------------------------------------------------------------

# 6. Student Intelligence Profile (SIP)

``` mermaid
classDiagram
    class StudentProfile {
        mastery_map
        mistake_patterns
        learning_style_weights
        difficulty_tolerance
        response_time_avg
        confidence_index
        streak_data
        revision_priority_queue
    }
```

------------------------------------------------------------------------

## Mastery Score Model

  Score Range   Status
  ------------- ------------
  0--40         Weak
  40--70        Developing
  70--85        Strong
  85--100       Mastered

Mastery persists across grades.

------------------------------------------------------------------------

# 7. Learning Style Detection

Behavior-based inference:

-   Better after diagram → Visual learner\
-   Strong with formulas → Analytical learner\
-   Asks "why" often → Conceptual learner\
-   Fast after example → Pattern learner

Weights: - visual_weight - analytical_weight - conceptual_weight -
pattern_weight

Highest weight determines explanation style.

------------------------------------------------------------------------

# 8. Dual-Track Learning Model

``` mermaid
flowchart TD
    A[Student Selects Topic] --> B{Check Prerequisites}
    B -- Sufficient Mastery --> C[Start Session]
    B -- Weak Prerequisite --> D[Offer 5-Min Booster]
    D --> C
```

AI does not block the student --- it guides intelligently.

------------------------------------------------------------------------

# 9. Recommendation Engine

After every session:

-   Update mastery_map
-   Recalculate revision_priority_queue
-   Identify weakest high-impact topics
-   Generate top 3 recommendations

Learn Page Sections: - Recommended For You - Continue Your Path -
Explore Freely

------------------------------------------------------------------------

# 10. Emotional Intelligence Layer

Rule-based tone adaptation:

-   3 wrong quickly → Supportive tone
-   High accuracy → Challenging tone
-   Long silence → Clarifying tone
-   Repeated confusion → Slow pacing

------------------------------------------------------------------------

# 11. Voice Interaction Model

``` mermaid
stateDiagram-v2
    [*] --> Explaining
    Explaining --> Interrupted
    Interrupted --> Clarification
    Clarification --> Resume
    Resume --> Explaining
```

Students can interrupt anytime.\
System stores explanation state and resumes seamlessly.

------------------------------------------------------------------------

# 12. Mini Test Architecture

-   5 mixed difficulty questions
-   Weighted scoring
-   Progressive difficulty inside test

After test: - Update mastery_score - Update confidence_index - Adjust
recommendation priority

------------------------------------------------------------------------

# 13. Gamification

-   Daily streak
-   Correct-answer streak

------------------------------------------------------------------------

# 14. System Component Architecture

``` mermaid
flowchart LR
    A[Frontend UI] --> B[Session Controller]
    B --> C[Teacher Agent]
    B --> D[Examiner Agent]
    B --> E[Supervisor Agent]
    E --> F[Student Profile Database]
    E --> G[Recommendation Engine]
```

------------------------------------------------------------------------

# 15. Core Philosophy

This is not an LMS.

This is a **Persistent AI Academic Companion**\
that adapts, remembers, guides, and evolves with the student.
