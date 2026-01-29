# Final Architecture & Strategy Report
**Project Name:** V (Vaathiyar AI)
**Domain:** Computer Science (DSA, OOPS, ML/DL)
**Core Philosophy:** Socratic, Visual, and Empathetic & Personalized Tutoring.

## 1. Executive Summary
This report defines the final architectural blueprint for Project V. It merges the **fluency** of the Khan Academy (GPT-4o) demo with the **robustness** of the user's provided Architecture Diagram, specifically adapted for the complexity of Computer Science education.

The goal is to move beyond "passive video watching" to **"Active Co-Creation"**, where the AI and student work together on a shared Canvas to solve Algorithms and Design Systems.

---

## 2. The Curriculum Adaptation (STEM -> CS)
The original STEM architecture components have been mapped to their Computer Science equivalents:

| STEM Component (Original) | CS / AI Component (Target) | Why? |
| :--- | :--- | :--- |
| **Math Solver** | **Code Execution Sandbox & Visualizer** | For DSA, we need to run code and *visualize* memory/pointers, not just solve equations. |
| **Shape Detection** | **Diagram Recognition (UML/Arch)** | For OOPS/System Design, the AI must understand boxes, arrows, and class relationships drawn by the user. |
| **Handwriting Rec** | **Pseudocode & Code Parsing** | Users often sketch logic before coding. The system must read "rough logic" as well as valid syntax. |
| **Knowledge Graph** | **Concept Dependency Graph** | Specific to CS: "Linked List" is a parent of "Tree", which is a parent of "Graph". This graph drives the curriculum. |

---

## 3. The "Active Canvas" Architecture

### A. The Socratic Loop (The Brain)
*   **Input**: User Voice + Canvas State (User just drew a node).
*   **Sentiment Layer (Research-Backed SER)**:
    *   **Architecture**: Hybrid CNN-LSTM Ensemble (as per *IJECE 2025*).
        *   *CNN* processes Spectrograms (Spatial features).
        *   *LSTM* processes MFCCs (Temporal evolution).
        *   *Fusion*: Combines both for 96% accuracy on emotion detection.
    *   **Features**:
        *   *Handcrafted*: MFCC 40-coeffs + OpenSmile (Pitch, Energy).
        *   *Deep Learning*: Wav2Vec 2.0 (Self-supervised representations).
    *   **Smart Gating ("The Cocktail Party Problem")**:
        *   The system uses VAD (Voice Activity Detection) + Intent Classification to ignore background noise and only respond to the user's tutor-directed speech.
    *   *Action*: Real-time adjustment of the "Socratic Rigor" based on Frustration/Boredom levels.
*   **Reasoning**:
    *   The **RAG Engine** retrieves the specific Algorithm definition from ingested textbooks (e.g., "Grokking Algorithms").
    *   The **System Prompt** ensures the AI asks: *"What happens to the `next` pointer here?"* instead of saying *"Move the pointer."*

### B. The Interactive Blackboard (The Interface)
This is not a static screen. It is a programmable environment.
1.  **Generative Visuals**: The AI can issue commands like `system.draw_array([1, 5, 9])` to instantly visualize data structures.
2.  **State Tracking**: The Board knows that `{ node_id: 5 }` is the "Root". If the user deletes it, the Board sends a specific event: `User_Deleted_Root`.
3.  **Collaborative Coding**: A split view with a **Monaco Editor** (for syntax) and a **Whiteboard** (for logic).

---

## 4. Technical Stack & Implementation Map

### Frontend (The "V" Interface)
*   **Framework**: Next.js 16 (App Router)
*   **Voice**: Web Speech API / Deepgram (for lower latency).
*   **Canvas**: `React-Konva` (for drawing shapes, nodes, trees).
*   **Code**: `Monaco Editor` (embedded in the canvas or split pane).

### Backend (The "V" Brain)
*   **Orchestrator**: Django 5.0 + Django Channels (WebSockets for real-time interaction).
*   **AI Engine**:
    *   **LLM**: GPT-4o / Gemini 1.5 Pro (via API).
    *   **RAG**: `pgvector` storing embeddings of:
        *   *DSA Textbooks* (Cormen, Bhargava)
        *   *Clean Code principles* (for OOPS)
        *   *Research Papers / PyTorch Docs* (for ML/DL)
*   **Knowledge Graph**: Using `NetworkX` (Python) to map prerequisite concepts (e.g., *Student must know 'Recursion' before 'DP'*).

---

## 5. Deployment & User Flow (The "North Star")

1.  **Dashboard**: User sees "Next Up: Binary Search Trees".
2.  **Session Start**: Canvas loads. AI says, *"Hello! Let's build a BST. Start by drawing the root node."*
3.  **Interaction**:
    *   *User*: Draws a circle.
    *   *AI (Vision/Canvas Event)*: Detects new node. *"Great. Now, where does the value '5' go if the root is '10'?"*
    *   *User*: Draws it on the right.
    *   *AI (Concept Check)*: *"Wait, remember the BST property? Left is smaller, Right is larger."*
4.  **Completion**: User completes the diagram. AI says, *"Perfect. Now let's write the Python class for this."* -> Editor opens.

## 6. Conclusion
This architecture delivers the **best outcome** by being hyper-specialized for CS. It doesn't just "talk"; it *visualizes algorithms* and *debugs logic* in real-time, creating a simulation of sitting next to a senior engineer or professor.
