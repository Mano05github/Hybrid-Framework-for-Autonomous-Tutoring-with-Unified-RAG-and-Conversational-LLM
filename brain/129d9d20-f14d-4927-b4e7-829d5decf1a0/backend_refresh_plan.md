# Backend Refresh Plan: Stabilizing the Brain

## Problem Analysis
1.  **Deprecated Library**: We are using `google.generativeai` (v1) which is now issuing "End of Support" warnings. This risks sudden breakage.
2.  **Fragile Error Handling**: If the AI fails (network/quota), the user sees nothing.
3.  **Stateless Orchestrator**: Expecting the "Context" to be sent perfectly every time. We need a more robust session state.

## Proposed Solution

### 1. Upgrade to `google-genai` (Official v2 SDK)
We will migrate from `google.generativeai` to the newer, cleaner `google-genai` library recommended by the warning.
```bash
pip install google-genai
pip uninstall google-generativeai
```

### 2. Refactor `SessionOrchestrator`
We will split the logic for cleaner maintenance:
*   **`AIService`**: Wrapper around the Google API. Handles retries, auth, and model selection.
*   **`SessionManager`**: Holds the current state (Code, Canvas Nodes, Chat History).
*   **`Orchestrator`**: Coordinates between Websocket ↔ SessionManager ↔ AIService.

### 3. Structured Error Protocol
The backend will send standardized error events to the frontend:
```json
{
  "type": "error",
  "payload": {
    "code": "AI_CONNECTION_FAILED",
    "message": "I'm having trouble connecting to my brain. Retrying..."
  }
}
```

### 4. Implementation Steps
1.  **Install** `google-genai`.
2.  **Create** `backend/learning_session/ai_service.py` (New Google client).
3.  **Update** `backend/learning_session/orchestrator.py` to use `ai_service`.
4.  **Verify** the `gemini-2.0-flash` model usage with the new SDK.

## Expected Outcome
*   No more console warnings.
*   Faster, more stable responses (v2 SDK uses gRPC/Proto under the hood usually).
*   User gets verified error feedback if something breaks.
