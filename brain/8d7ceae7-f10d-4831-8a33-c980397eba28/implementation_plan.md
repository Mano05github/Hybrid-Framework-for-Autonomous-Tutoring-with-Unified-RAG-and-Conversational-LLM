---
name: STEM Tutoring System (Lite Edition)
overview: A focused, open-access STEM tutoring platform. It removes barriers like login/registration to treat the user immediately as a student. The experience centers on three core views: a personalized **Dashboard**, a structured **Lessons** browser, and the immersive **Interactive Blackboard** where the AI Voice Assistant (visualized as 4 pulsing dots) helps solve problems and visualize concepts.
todos:
  - id: frontend-setup-lite
    content: Setup Next.js with the 3 main routes: `/` (Dashboard), `/lessons`, and `/blackboard`.
    status: pending
  - id: dashboard-ui
    content: Create a welcoming Dashboard showing "Recent Topics" and "Recommended Paths" (using local storage for persistence instead of DB auth).
    status: pending
  - id: lessons-ui
    content: Build a curriculum browser (The "Map" of knowledge) to select topics.
    status: pending
  - id: blackboard-core
    content: Develop the full-screen `react-konva` Canvas with the **4-dots Voice Visualizer** fixed at the bottom.
    status: pending
  - id: voice-interaction-layer
    content: Implement ASR (Speech-to-Text) & TTS with the pulsing animation synced to voice amplitude.
    status: pending
  - id: backend-services
    content: Setup Django/FastAPI for LLM orchestration and RAG (no user auth middleware needed).
    status: pending
---

# STEM Tutoring System Development Plan (Simplified)

## Core Philosophy: "Frictionless Learning"
No signup. No login. The user opens the app and is learning within seconds. The "Teacher" is always there, represented by the calm, pulsing dots on the Blackboard.

## Architecture

### 1. The Frontend (Next.js)
*   **No Auth Wrapper**: Public access to all pages.
*   **State**: Use `localStorage` or `IndexedDB` on the client to remember "Recent Lessons" or "Settings" so the dashboard feels personal without a login.

### 2. The Three Pillars (Pages)

#### A. The Dashboard (`/`)
*   **Goal**: Orient the user.
*   **Elements**:
    *   **Welcome Banner**: "Welcome back, Student."
    *   **Quick Start**: Continue where you left off.
    *   **Stats**: Simple session-based stats (e.g., "Time Learnt Today").

#### B. The Lessons (`/lessons`)
*   **Goal**: exploration.
*   **Elements**:
    *   A visual tree or grid of STEM topics (Physics, Math, Chemistry).
    *   Search bar to find specific concepts.

#### C. The Interactive Blackboard (`/blackboard`)
*   **Goal**: The Deep Work zone.
*   **Layout**:
    *   **Canvas**: Covers 100% of the screen.
    *   **The Interface**: Minimalist. Inspired by the **Khan Academy + GPT-4o Demo**.
    *   **The Voice Agent**: **4 Dots** centered at the bottom. They act as the primary interface button.
        *   *Idle*: Gently breathing.
        *   *Listening*: Expanding/Contracting with volume.
        *   *Thinking*: Spinning/Color shift.
        *   *Speaking*: Pulsing aggressively.
    *   **AI Capabilities**: The AI "sees" the canvas (like the demo) and can draw/highlight to guide the user.

## Data Flow (Simplified)
`User Speech` -> `Browser STT` -> `Backend LLM` -> `Browser TTS` + `Canvas Draw Command`
