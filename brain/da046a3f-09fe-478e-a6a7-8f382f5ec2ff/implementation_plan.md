# Backend Implementation Plan - Personal Tutoring Website

## Goal Description
Establish the backend infrastructure using Python and Django. This includes setting up the database with vector support for RAG, implementing user authentication, and preparing the architecture for AI-driven content generation and adaptation.

## User Review Required
> [!IMPORTANT]
> **Database Requirement**: This plan assumes a local PostgreSQL installation is available. The `pgvector` extension will be needed for RAG features. Please ensure PostgreSQL is installed on your machine or accessible via a connection string.

## Proposed Changes

### Project Initialization
#### [NEW] [backend/structure](file:///d:/final year project/V/backend)
- Create a `backend` directory in the root.
- Initialize a new Django project named `config`.
- Create a `requirements.txt` with dependencies: `django`, `djangorestframework`, `psycopg2-binary`, `pgvector`, `openai`, `google-generativeai`, `langchain`.

### Authentication Enhancements
#### [MODIFY] [users/models.py](file:///d:/final year project/V/backend/users/models.py)
- **Student ID**: Add `student_id` field to `User` model.
    - Format: `SID-YYYY-<RandomAlphanumeric>` (e.g., `SID-2024-X9A2`).
    - Auto-generated on creation. Unique and read-only.

#### [MODIFY] [users/serializers.py](file:///d:/final year project/V/backend/users/serializers.py)
- **Registration Logic**:
    - **Password**: Enforce regex `^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$` (8+ chars, alphanumeric, 1 special).
    - **Username**: Enforce regex `^[a-zA-Z0-9]+[@._][a-zA-Z0-9]+$` (Alphanumeric + specific special char logic).
    - **Email**: Ensure valid format.

#### [NEW] [users/views.py](file:///d:/final year project/V/backend/users/views.py)
- **Custom Login View**:
    - Accept `login_id` and `password`.
    - Check if `login_id` is an email or username.
    - Authenticate and return tokens/session.

### Frontend Integration
#### [NEW] [frontend/lib/api.ts](file:///d:/final year project/V/frontend/lib/api.ts)
- Create Axios instance with base URL `http://127.0.0.1:8000/api/`.
- Add interceptors for token management (if needed later).

#### [MODIFY] [frontend/app/auth/register/page.tsx](file:///d:/final year project/V/frontend/app/auth/register/page.tsx)
- Connect form submission to `/users/register/`.
- Handle success (redirect to login) and error states (display validation errors).

#### [MODIFY] [frontend/app/auth/login/page.tsx](file:///d:/final year project/V/frontend/app/auth/login/page.tsx)
- Connect form submission to `/users/login/`.
- Store user data/tokens in Context/LocalStorage.
- Redirect to Dashboard.

### AI & RAG Integration (Strict Syllabus Policy)
#### [NEW] [ai_engine/models.py](file:///d:/final year project/V/backend/ai_engine/models.py)
- **Embedding Model**: `KnowledgeChunk`.
    - `content`: Text content (Max 500 tokens).
    - `embedding`: VectorField (768 dimensions for Gemini).
    - `source_url`: URL (if scraped).
    - `is_approved`: Boolean (Default False, requires manual approval).
    - `topic`: Link to `core.Topic` (Syllabus alignment).

#### [NEW] [ai_engine/services.py](file:///d:/final year project/V/backend/ai_engine/services.py)
- **EmbeddingService**:
    - Use `models/text-embedding-004` (Gemini).
    - Chunking logic: 200-500 tokens.
- **RAGService**:
    - **Logic**: Retrieve ONLY approved chunks.
    - **System Prompt**:
        - Role: "Calm and professional teacher".
        - Rule: "Use ONLY retrieved context."
        - Fallback: "This topic is not available in your current syllabus."
    - **Security**: Prompt injection defense layers.

#### [NEW] [ai_engine/ingestion.py](file:///d:/final year project/V/backend/ai_engine/ingestion.py)
- **Scraping Policy**:
    - Functionality to scrape -> clean -> chunk -> simplify.
    - **CRITICAL**: Scraped content is saved with `is_approved=False`.
    - Must be manually reviewed via Admin panel before becoming active in RAG.
- **PDF Ingestion**:
    - Tool: `pypdf`.
    - Script: `ingest_pdf.py`.
    - Extracts text page-by-page, chunks it, and saves as "Draft".

## Dashboard Modernization
- **Design Philosophy**: Glassmorphism, Dark Mode, Bento Grid Layout (Responsive).
- **Components**:
    - **Welcome Header**: Personalized greeting.
    - **Stats Overview**: Simple cards (Lessons Completed, Streak, XP).
    - **Recommended Course**: Dynamic card linking to "Algorithms" (RAG Topic).
    - **Recent Activity**: List of last accessed lessons.
- **Backend Support**:
    - **Endpoint**: `/api/core/dashboard/` (Aggregates usage stats and suggested topics).

## Algorithms Flow & Enhancements
- **Data Structure**:
    - Split "Algorithms" Topic into specific `Lesson` entries (Binary Search, Quicksort, etc.) via seeding script.
- **New Pages**:
    - `/algorithms`: Lists all algorithm lessons with progress bars.
    - `/editor`: Code Editor interface (Shortcut from Dashboard).
- **Dashboard Updates**:
    - **Algorithms Tile**: Blue/Purple gradient card linking to `/algorithms`.
    - **Code Editor Tile**: Quick access to coding sandbox.
    - **Resume Learning**: Dynamic card showing the specific lesson last accessed.

## Verification Plan

### Automated Tests
- **Server Startup**: Run `python manage.py runserver` to ensure the project initializes correctly.
- **Database Connection**: Run `python manage.py migrate` to verify PostgreSQL connection and migration application.
- **API Test**: Use `curl` or Postman to test the registration endpoint.
- **Vector Search Test**: Create a dummy chunk, embed it, and verify it can be retrieved via similarity search.

### Manual Verification
1.  Run the server: `python manage.py runserver`
2.  Navigate to `http://localhost:8000/admin` to verify Admin interface.
3.  Create a superuser and log in.
