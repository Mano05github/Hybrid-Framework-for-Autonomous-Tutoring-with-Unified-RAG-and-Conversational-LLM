# Vision & Strategic Alignment Report
**Project V vs. Khan Academy (GPT-4o Demo)**

## 1. Executive Summary
The analyzed video demonstrates the specific ideal user experience: a **Socratic**, **Multi-modal**, and **Empathetic** AI tutor. Project V aims to replicate this quality of interaction but enhance it with **specialized domain knowledge (RAG)** and a **richer visual canvas**.

This report analyzes the gaps between the demo and our current trajectory and proposes specific technical enhancements to ensure Project V achieves the "best outcome."

---

## 2. Comparative Analysis

| Feature | Khan Academy (Demo) | Project V (Current State) | Project V (Target State) |
| :--- | :--- | :--- | :--- |
| **Interaction Mode** | Voice + Screen Sharing (Visual Perception) | Voice + Canvas (Planned) | **Voice + Active Canvas Interaction** |
| **Knowledge Source** | General GPT-4o Model | General LLM + Basic RAG | **Curated RAG (Textbooks) + Real-time Web Search** |
| **Teaching Style** | Socratic (Prompts & Nudges) | General QA (Default LLM behavior) | **Enforced Socratic System Prompting** |
| **Visuals** | Static User Screen (AI "sees" user screen) | Static Whiteboard (Planned) | **Generative Whiteboard (AI "draws" concepts)** |
| **State Awareness** | Limited to current conversation context | Stateless (Per request) | **Persistent Lesson State (Tracking Student Progress)** |

---

## 3. Strategic Enhancements

To win against generic chatbot implementations, Project V must leverage its **Canvas Environment**. The AI shouldn't just *see* what the user is doing (like the video); it should *co-create* with the user.

### A. The "Active Canvas" (The Differentiator)
In the video, the AI asks, "Can you identify the hypotenuse?". The student points with their mouse.
**In Project V**, we can go further:
*   **AI-Driven Drawing**: If the user is learning "Binary Trees," the AI should be able to send a command to **draw a tree on the canvas** in real-time.
*   **Visual Highlighting**: When the AI asks "Which node is the root?", and the user clicks a node, the canvas should visually highlight it, and the AI should receive that specific node's ID, not just "user clicked screen."

### B. "Deep Context" RAG (The Brain)
The video shows generic math help. Project V has a secret weapon: **Specific Ingested Content**.
*   **Implementation**: Instead of just asking generic questions, the RAG engine should retrieve *specific examples* from the uploaded PDFs (e.g., "Grokking Algorithms").
*   **Benefit**: The AI teaches using the *exact definitions and metaphors* from the course material, ensuring consistency with the curriculum.

### C. The Socratic Loop Engine (The Personality)
We need to engineer the System Prompt to strictly forbid "Answer Giving."
*   **Current Risk**: Standard LLMs love to be helpful and give answers immediately.
*   **Solution**: Implement a "Tutor Persona" middleware.
    *   *Input*: User asks "How do I reverse a list?"
    *   *Internal Thought*: User wants code. I should not give code. I should ask about the first step.
    *   *Output*: "Think about the last element. Where should it go in the new list?"

---

## 4. Technical Roadmap Updates

To achieve this "North Star" vision, we need to add specific capabilities to our roadmap:

1.  **Canvas-Backend Protocol**:
    *   Define a JSON schema for the backend to *manipulate* the frontend canvas (e.g., `{ "action": "draw_shape", "type": "circle", "x": 100, "y": 100 }`).
2.  **Lesson State Manager**:
    *   The Backend needs to know "We are currently on Step 3 of the 'Recursion' lesson."
3.  **Vision/Multimodal Bridge**:
    *   If the user draws on the canvas, send the *canvas state (JSON/Image)* to the LLM so it "sees" the user's diagram, replicating the video's capability.

## 5. Conclusion
The Khan Academy demo sets a high bar for *fluency*. Project V will match that fluency through voice but **exceed it in interactivity** by making the learning environment (the Canvas) programmable and deeply integrated with the AI's "brain."
