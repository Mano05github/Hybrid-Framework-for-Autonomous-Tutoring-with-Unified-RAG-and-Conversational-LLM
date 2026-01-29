# Backend Setup Walkthrough

## Overview
We have successfully initialized the backend for the Personal Tutoring Website using Django and PostgreSQL. The foundational apps and API endpoints are in place.

## Features Implemented

### 1. Database Connection
- Connected to local PostgreSQL database `Vaathi`.
- Applied migrations for Users and Core models.

### 2. User Authentication
- **Endpoint**: `/api/users/register/` (POST)
    - **Validations**:
        - Password: Min 8 chars, 1 letter, 1 number, 1 special char (`@$!%*#?&`).
        - Username: Alphanumeric + at least one special char (`@._`).
    - **Auto-Generation**: Creates a unique `student_id` (e.g., `SID-2025-X9A2`).
- **Endpoint**: `/api/users/login/` (POST)
    - Supports login matching either **Username** OR **Email**.
- **Endpoint**: `/api/users/me/` (GET) - Get current user profile.
- **Model**: Custom `User` model with `is_student`, `is_tutor` flags, and `student_id`.

### 3. Frontend-Backend Integration
- **API Client**: `frontend/lib/api.ts` configured for `http://127.0.0.1:8000/api/`.
- **Pages Connected**:
    - **Registration**: Connected to `/users/register/`. Handles errors and redirects.
    - **Login**: Connected to `/users/login/`. Supports Username/Email.

### 4. UI Enhancements
- **Global Sidebar**:
    - Accessible via User Avatar button (top-right).
    - Contains links to Dashboard, Learning, Profile, Settings.
    - **Conditional Rendering**: Automatically hidden on Login/Register pages using `LayoutWrapper`.

### 5. AI & RAG Integration
- **Engine**: Google Gemini (`gemini-1.5-flash` + `text-embedding-004`).
- **Database**: PostgreSQL with `pgvector` (768 dimensions).
- **RAG Logic**:
    - Queries match against **Approved** `KnowledgeChunks`.
    - Strict System Prompt enforces "Syllabus-Only" answers.
- **Content Sources**:
    - **Files**: PDF Loading via `pypdf` (e.g., *Grokking Algorithms*).
    - **Validation**: Auto-draft, Manual Approval workflow.
- **Frontend**:
    - **Chat Interface**: Located at `/learn`.
    - Real-time streaming (simulated via API wait) and Source Citation.

### 6. Dashboard Modernization
- **Backend API**: `/api/core/dashboard/` provides aggregated stats and recommendations.
- **Frontend Design**: 
    - **Bento Grid**: Responsive layout for statistics.
    - **Glassmorphism**: Dark UI with blurred overlays using Tailwind CSS.
    - **Dynamic Data**: Shows real user streak, progress, and personalized topic suggestions (e.g., "Algorithms").

### 7. Core Learning Structure
- **Models**:
    - `Subject`: Broad categories (e.g., Programming).
    - `Topic`: Specific modules (e.g., Variables).
    - `Lesson`: Educational content blocks.
    - `Quiz` & `Question`: Assessment tools.
    - `UserProgress`: Tracks what users have completed.
- **API Endpoints** (Read-Only/Public):
    - `/api/core/subjects/`
    - `/api/core/topics/`
    - `/api/core/lessons/`
    - `/api/core/quizzes/`
- **API Endpoints** (Authenticated):
    - `/api/core/progress/` (Manage your own progress)

## How to Run
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Run the server:
   ```bash
   python manage.py runserver
   ```
3. Access the API at `http://localhost:8000/api/core/`

## Next Steps
- Implement AI Engine integration (OpenAI/Gemini).
- Set up RAG (Retrieval-Augmented Generation) with `pgvector`.
