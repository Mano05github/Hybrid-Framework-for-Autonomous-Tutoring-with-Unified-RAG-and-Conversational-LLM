# Architecture Transition Report: Integrating the Old with the New

This report analyzes how our **previously implemented strategies** (Phase 1-6) evolve into the **Phase 7 Multi-Agent System**.

**Executive Summary**: We are **not** rewriting the core logic. We are strictly **re-organizing** who calls it. The "Brain" (Llama 3.2) remains the same.

---

## 1. The "Teacher Agent": Still Llama 3.2?
**YES.**
*   **Strategy**: In Phase 5a, we built the `LLMFactory` and `OllamaProvider`.
*   **New Flow**: The `TeacherAgent` will simply call `LLMFactory.get_provider()` to get the Llama 3.2 instance.
*   **Benefit**: The agent inherits all the cost-saving and privacy benefits we already built.

## 2. Component Mapping matrix

| Previous Component (Phase 1-6) | New Agent Owner (Phase 7) | Role Change? |
| :--- | :--- | :--- |
| **`SessionOrchestrator`** | **`SupervisorAgent`** | **Major**: Instead of doing everything, it now just routes messages to specialist agents. |
| **`RAGRetriever`** (ChromaDB) | **`RAGAgent`** | **Minor**: The logic (`get_relevant_context`) moves to a dedicated agent tool. |
| **`EmotionService`** (Librosa) | **`EmpathAgent`** | **None**: The service is wrapped in an agent interface to continuously monitor audio. |
| **`OllamaProvider`** (Llama 3.2) | **All Generation Agents** | **Shared**: Used by Teacher, Examiner, and Coder for text generation. |
| **`CodeExecutor`** (Pyodide) | **`CoderAgent`** | **None**: The frontend execution logic remains; the agent just prepares the code block. |

---

## 3. How Specific Strategies Adapt

### A. The "Factory Pattern" Strategy (Phase 5a)
*   **Old**: Orchestrator called `LLMFactory`.
*   **New**: **Every** agent (Teacher, Examiner, Coder) calls `LLMFactory`.
*   **Result**: If we switch `AI_ENGINE_MODE=gemini`, the **entire swarm** upgrades instantly. Zero code change.

### B. The "RAG" Strategy (Phase 5b)
*   **Old**: `Orchestrator` injected context into System Prompt manually.
*   **New**: The `TeacherAgent` requests facts from `RAGAgent`.
*   **Improvement**: The Teacher can decide *not* to use RAG for simple "Hi" messages, saving latency.

### C. The "Voice" Strategy (Phase 6b)
*   **Old**: `Consumer` called `TTSService` blindly on output.
*   **New**: `SupervisorAgent` receives the final text from Teacher/Coder and passes it to `TTSService`.
*   **Result**: Voice output remains consistent regardless of which agent generated the text.

## 4. Conclusion
The "Agentic" shift is a **Logic Layer** change, not a **foundational** change. We keep all our libraries (LangChain, Chroma, EdgeTTS) and simply give them "Personalities" to manage them better.
