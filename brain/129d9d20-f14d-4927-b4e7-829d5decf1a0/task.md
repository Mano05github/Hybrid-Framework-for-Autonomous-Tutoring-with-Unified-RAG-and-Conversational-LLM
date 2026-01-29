# Redesign Task List

- [/] Analyze current frontend structure <!-- id: 0 -->
- [ ] Create Implementation Plan <!-- id: 1 -->
    - [ ] Define global theme (colors, fonts) <!-- id: 2 -->
    - [ ] Plan Landing Page changes <!-- id: 3 -->
    - [ ] Plan Courses Page changes <!-- id: 4 -->
    - [ ] Plan Contact Page changes <!-- id: 5 -->
    - [ ] Plan Blog Page changes <!-- id: 6 -->
- [ ] User Review & Approval <!-- id: 7 -->
- [/] Execute Redesign <!-- id: 8 -->
    - [x] Setup Global Styles/Theme <!-- id: 9 -->
    - [x] Implement Landing Page <!-- id: 10 -->
    - [x] Implement Courses Page <!-- id: 11 -->
    - [x] Implement Contact Page <!-- id: 12 -->
    - [x] Implement Blog Page <!-- id: 13 -->
    - [x] Dashboard Redesign (Layout & Stats reset) <!-- id: 15 -->
    - [x] Dynamic Dashboard Calendar <!-- id: 16 -->
    - [x] Code Editor Theme Update <!-- id: 17 -->
- [x] Verification <!-- id: 14 -->
- [x] **Phase 2: Active Canvas Transformation** <!-- id: 18 -->
    - [x] Create `ActiveWhiteboard` Component (react-konva) <!-- id: 19 -->
    - [x] Extract `CodeEditor` Component <!-- id: 20 -->
    - [x] Implement Split-Pane Layout in `/learn` <!-- id: 21 -->
    - [x] Integrate Voice & Chat as Sidebars <!-- id: 22 -->
    - [x] Connect Canvas to "System Prompt" (Stub - Moved to Phase 4) <!-- id: 23 -->
    - [x] Implement Multi-Language Editor <!-- id: 24 -->

- [x] **Phase 4: Backend & AI Integration**
    - [x] **Backend Assessment & Setup**
        - [x] Analyze existing `backend` directory
        - [x] Setup/Verify Django Environment
        - [x] Verify/Install `channels` for WebSockets
    - [x] **Real-time Communication**
        - [x] Create `LearningConsumer` (ASGI)
        - [x] Establish WebSocket connection in Frontend (`SessionLayout`)
    - [x] **AI "Socratic" Integrated**
        - [x] Connect OpenAI/Gemini API (Updated to `google-genai` SDK)
        - [x] Build Context Manager (Canvas + Code State)
        - [x] Implement Sentiment Analysis (Basic Stub/AI logic implemented)

- [x] **Phase 5: Code Execution Engine**
    - [x] **Strategy Selection**: Choose safe execution method (Client-side Pyodide vs Server-side Piston/Docker).
    - [x] **Implementation**: Connect "Run" button to execution logic.
    - [x] **Output Display**: Show stdout/stderr in the Editor console.

- [x] **Phase 5b: The "Expert" Brain (RAG & Prompts)**
    - [x] **LLM Architecture**: Refactor to Dual Engine (Local Llama / Cloud Gemini).
    - [x] **RAG System**: Implement ChromaDB + LangChain for PDF ingestion.
    - [x] **Retrieval Integration**: Connect `retriever.py` to Orchestrator.
    - [ ] **RAG Optimization**: Reduce latency (k=1) or implement Streaming.

- [/] **Phase 6: The "Sensitive" Tutor (Voice & Emotion)**
    - [x] **The Ears (Input)**: Implement `useAudioRecorder` + VAD + EmotionService.
    - [ ] **The Mouth (Output)**: Implement `edge-tts` for Voice Synthesis.
    - [ ] **The Feeback Loop**: Connect Emotion and Voice to System Prompt (e.g. "Speak softly if student is frustrated").

- [x] **Phase 7: The "Swarm" (Multi-Agent Architecture)**
    - [x] **Infrastructure**: Install `langgraph` and set up `AgentState`.
    - [x] **Supervisor**: Build `SupervisorAgent` (The Router).
    - [x] **The "Librarian"**: Wrap `RAGRetriever` into `RAGAgent` (Teacher Tool).
    - [ ] **The "Analyst"**: Implement Memory Agent for user mastery.
    - [x] **The "Visionary"**: Implement Image Analysis Agent. <!-- id: 25 -->

- [/] **Phase 8: The "Adaptive" Coach (Meta-Cognition)**
    - [x] **Strategy Design**: Define BKT, IRT, & ZPD methodologies. <!-- id: 26 -->
    - [ ] **Database Schema**: Implement `StudentProfile`, `ConceptNode`, `MasteryState`. <!-- id: 27 -->
    - [ ] **The "Analyst"**: Implement logic to update BKT probabilities from logs. <!-- id: 28 -->
    - [ ] **The "Coach"**: Implement ZPD-based content selection strategy. <!-- id: 29 -->

- [/] **Phase 9: The "Librarian Swarm" (RAG Upgrade)**
    - [x] **Strategy Design**: Draft "Omni-RAG" architecture. <!-- id: 32 -->
    - [ ] **Retrieval**: Implement `HybridRetriever` (Chroma+BM25) & `ReRanker`. <!-- id: 33 -->
    - [ ] **Reasoning**: Implement `CriticAgent` (Self-Correction loop). <!-- id: 34 -->
    - [ ] **Integration**: Connect to Graph & Personalization. <!-- id: 35 -->
