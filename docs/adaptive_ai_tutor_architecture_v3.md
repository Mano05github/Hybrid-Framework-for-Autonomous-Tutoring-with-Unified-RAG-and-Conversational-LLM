# Adaptive AI Tutor Architecture v3

## (Tree-Based Theory Mode + Full Canvas Application Mode)

------------------------------------------------------------------------

# 1. High-Level Learning Funnel

``` mermaid
flowchart TD
    A[Subject Hub] --> B[Topic Page]
    B --> C[Teaching Session]
    C --> D{Content Type}
    D -->|Concept / Theory| E[Tree Visualization Mode]
    D -->|Formula / Problem / Derivation| F[Full Canvas Mode]
```

------------------------------------------------------------------------

# 2. Teaching Session Architecture

The Teaching Session dynamically switches between two cognitive modes:

-   🧠 Structural Understanding (Tree Mode)
-   ✍️ Procedural Execution (Canvas Mode)

``` mermaid
stateDiagram-v2
    [*] --> TreeMode
    TreeMode --> CanvasMode : Formula Introduced
    CanvasMode --> TreeMode : Concept Recap
```

------------------------------------------------------------------------

# 3. Tree Visualization Mode (Theory Mode)

Used when: - Explaining definitions - Explaining theoretical
structures - Describing components - Showing relationships

Canvas Behavior: - Live-growing concept tree - Expandable nodes -
Highlight active concept - Minimal distraction UI

### Example: Newton's Laws

``` mermaid
graph TD
    A[Newton's Laws of Motion] --> B[First Law]
    A --> C[Second Law]
    A --> D[Third Law]

    B --> B1[Inertia]
    B --> B2[Net Force = 0]
    B --> B3[Constant Velocity]

    C --> C1[F = ma]
    C --> C2[Force]
    C --> C3[Acceleration]
```

------------------------------------------------------------------------

# 4. Full Canvas Mode (Application Mode)

Triggered when: - Formula appears - Numerical problem begins -
Derivation starts - Diagram construction required

Canvas becomes: - Interactive whiteboard - Step-by-step solution
workspace - Graph plotting surface - Drawing environment

### Example Transition

``` mermaid
sequenceDiagram
    participant Teacher
    participant Canvas

    Teacher->>Canvas: Explain Concept (Tree Mode)
    Teacher->>Canvas: Introduce Formula F = ma
    Canvas-->>Teacher: Switch to Full Canvas Mode
    Teacher->>Canvas: Solve Example Step-by-Step
```

------------------------------------------------------------------------

# 5. Intelligent Mode Switching Logic

``` mermaid
flowchart LR
    A[Content Analyzer] --> B{Detect Content Type}
    B -->|Concept| C[Render Tree Mode]
    B -->|Formula / Problem| D[Render Canvas Mode]
```

Pseudo-logic:

    if content_type == "concept":
        render_mode = "tree"
    elif content_type in ["formula", "problem", "derivation"]:
        render_mode = "whiteboard"

------------------------------------------------------------------------

# 6. UI Transition Behavior

When switching modes:

Tree shrinks → slides → expands into whiteboard.

Smooth animated transition ensures: - Cognitive continuity - Premium UX
feel - Reduced mental friction

------------------------------------------------------------------------

# 7. Final Structured Learning Architecture

``` mermaid
flowchart TD
    A[Subject Hub]
    B[Topic Page]
    C[Teaching Session]

    A --> B
    B --> C

    C --> D[Tree Mode - Understanding]
    C --> E[Canvas Mode - Application]

    D --> E
    E --> D
```

------------------------------------------------------------------------

# Core Design Philosophy

-   Theory builds structure.
-   Problems build skill.
-   Tree organizes knowledge.
-   Canvas operationalizes knowledge.

This architecture separates cognition into: 1. Structural Knowledge
Encoding 2. Procedural Skill Execution

Result: Cleaner learning funnel, higher retention, adaptive
intelligence-ready system.
