# LLM Engine Architecture Refactor

## Goal
Decouple the "Intelligence" from the "Orchestrator" to allow dynamic switching between **Google Gemini** (Cloud) and **Mistral** (Local/Ollama) to manage API quotas.

## Directory Structure
```text
backend/llm_engine/
├── __init__.py
├── interfaces.py          # Abstract Base Class (LLMProvider)
├── factory.py             # LLMFactory (Returns the correct provider)
└── providers/
    ├── __init__.py
    ├── google_gemini.py   # Migrated AIService logic
    └── local_mistral.py   # New Ollama adapter
```

## Step-by-Step Implementation

### 1. The Interface (`interfaces.py`)
Defines the contract: `generate_response(prompt: str) -> str`.

### 2. The Cloud Provider (`providers/google_gemini.py`)
This will basically be the current `ai_service.py` but renamed and inheriting from the interface.

### 3. The Local Provider (`providers/local_mistral.py`)
Uses `requests` to hit `http://localhost:11434/api/generate` (Ollama default).

### 4. The Factory (`factory.py`)
Reads `LLM_PROVIDER` from `os.environ`.
- If `gemini`: Returns `GoogleGeminiProvider`.
- If `mistral`: Returns `LocalMistralProvider`.

### 5. Integration (`orchestrator.py`)
Replace:
```python
self.ai_service = AIService()
```
With:
```python
from llm_engine.factory import LLMFactory
self.llm = LLMFactory.get_provider()
```

## Impact Analysis
- **Low Risk**: The Orchestrator just calls `.generate_response()`, so swapping the backend is transparent.
- **Dependency**: Requires `ollama` running locally for the Mistral path to work.
