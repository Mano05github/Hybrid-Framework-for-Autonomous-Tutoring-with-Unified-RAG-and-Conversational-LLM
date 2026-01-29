# The Brain: Backend Architecture Guide

## 1. The Big Picture
We are building a **Real-Time Socratic Tutor**.
Unlike a normal chatbot (which just replies to text), this Tutor:
1.  **Watches your code** as you type.
2.  **Remembers** your past mistakes.
3.  **Acts proactively** (it can intervene if you are stuck).

To do this, we moved away from "Request-Response" (HTTP) to "Always Connected" (WebSockets).

## 2. The "4-Layer Brain"
We organized the backend into 4 distinct layers to keep it clean and safe.

### Layer 1: The Gateway (The Ear)
*   **File**: `backend/learning_session/consumers.py`
*   **Role**: **Receptionist**.
*   **What it does**:
    *   It sits between the User and the Server.
    *   It listens for incoming WebSocket messages.
    *   It sorts them: *"This is a Chat Message"* vs *"This is a Code Edit"*.
    *   **Analogy**: It's the person at the front desk who directs your call.

### Layer 2: The Manager (The Cortex)
*   **File**: `backend/learning_session/orchestrator.py`
*   **Role**: **Context Manager**.
*   **What it does**:
    *   It holds the **Source of Truth** for the session.
    *   It keeps a history of:
        *   `code_history`: What the user wrote.
        *   `chat_history`: What was said.
        *   `topic`: "Binary Search Trees".
    *   When you ask "Why isn't this working?", the Manager looks at your *Code History*, bundles it with your question, and creates a "Prompt" for the AI.
    *   **Analogy**: The project manager who knows all the project details before asking the expert for help.

### Layer 3: The Voice (The Service)
*   **File**: `backend/learning_session/ai_service.py`
*   **Role**: **API Wrapper**.
*   **What it does**:
    *   It is the **only** part that talks to Google.
    *   It handles API Keys, Libraries (`google-genai`), and Errors.
    *   If Google is down, this layer catches the fire so the whole server doesn't crash.
    *   **Analogy**: The telephone operator. It just makes the call.

### Layer 4: The Intelligence (The Cloud)
*   **Component**: **Google Gemini 2.0 Flash**
*   **Role**: **The Raw Brain**.
*   **What it does**:
    *   Generates the actual text response based on the prompt we sent.

## 3. The Lifecycle of a "Hello"
Here is exactly what happened when you typed "Hello":

1.  **YOU**: Type "Hello" -> Press Send.
2.  **FRONTEND**: Sends JSON `{"type": "chat_message", "message": "Hello"}` over WebSocket.
3.  **CONSUMER (Layer 1)**: Receives JSON. Sees "chat_message". Calls the Manager.
4.  **MANAGER (Layer 2)**:
    *   Updates History: `User: Hello`.
    *   Checks Context: "User is learning BST. Code is empty."
    *   Creates Prompt: *"You are a tutor. User says Hello. Context is BST."*
    *   Calls Service.
5.  **SERVICE (Layer 3)**: Sends prompt to Google `gemini-2.0-flash`.
6.  **GOOGLE**: Returns *"Hello! Ready to code?"*
7.  **MANAGER**: Updates History: `AI: Hello...`. Returns text to Consumer.
8.  **CONSUMER**: Sends JSON `{"type": "ai_response", "message": "Hello!..."}` to Frontend.
9.  **YOU**: See the message appear.

## 4. Why this is better?
*   **Safety**: If we want to switch to OpenAI or Mistral later, we **only** change `ai_service.py`. The rest of the app doesn't know (or care) which AI is used.
*   **Context**: The AI isn't just "guessing". The Manager ensures the AI *always* sees your latest code, so it gives accurate advice.
