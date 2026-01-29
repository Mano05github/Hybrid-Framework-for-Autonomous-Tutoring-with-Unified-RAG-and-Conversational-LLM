# Test Suite for AI-Powered Tutoring System

This folder contains all test files for validating the implementation of Gaps 3, 4, and 5, as well as utility tests for external services.

## Test Files

### Gap Validation Tests (Keep These!)

#### 1. **test_gap3.py** - Socratic Coder Agent Tests
**Purpose:** Validate Gap 3 implementation (5-level hint system, sandbox execution, struggle detection)

**Run:** `python tests/test_gap3.py`

**Tests:**
- Syntax error detection
- Logic error detection  
- Struggle detection with idle time
- Hint level progression (adaptive to user skill)
- Database logging for submissions

**Requirements:** Django setup, test user, CodingProblem records in database

---

#### 2. **test_gap4.py** - Adaptive Empath Agent Tests
**Purpose:** Validate Gap 4 implementation (emotion detection, interventions, teaching strategies)

**Run:** `python tests/test_gap4.py`

**Tests:**
- Emotion intensity classification (mild/moderate/strong)
- Intervention decision matrix (pacing/visualization/branching)
- Database logging (EmotionEvent creation)
- Teaching strategy effectiveness tracking
- Sentiment analysis (keyword-based)

**Requirements:** Django setup, test user

---

#### 3. **test_gap5.py** - Always-On Visionary Agent Tests
**Purpose:** Validate Gap 5 implementation (telemetry, heuristics, forecasting, canvas monitoring)

**Run:** `python tests/test_gap5.py`

**Tests:**
- Telemetry snapshot capture (mouse, keyboard, idle time)
- Anomaly detection (idle spikes, error cascades, velocity drops)
- Canvas monitoring and diagram validation
- Strategic forecasting (trajectory prediction)
- Triple-Check coordination (all 3 agents)

**Requirements:** Django setup, test user, active learning session

---

### Component Tests (Keep These!)

#### 4. **test_sandbox.py** - Code Sandbox Tests
**Purpose:** Test RestrictedPython sandbox for Gap 3 (security, timeout, import blocking)

**Run:** `python tests/test_sandbox.py`

**Tests:**
- Correct code execution
- Syntax error handling
- Dangerous operation blocking (file access)
- Import blocking
- Infinite loop timeout (5s limit)
- Output comparison logic

**Requirements:** Django setup

---

#### 5. **test_empath.py** - Empath Engine Tests
**Purpose:** Test transformer-based sentiment analysis and emotion fusion for Gap 4

**Run:** `python tests/test_empath.py`

**Tests:**
- Transformer sentiment analysis (DistilBERT)
- Multi-signal emotion fusion (pause + sentiment + errors)
- Intervention decision strategies
- Topic graph traversal for branching
- Complete emotion assessment workflow

**Requirements:** Django setup, transformer models loaded

---

### External Service Tests (One-Time Use - Safe to Delete After Initial Setup)

#### 6. **test_gen.py** - Google Gemini API Test
**Purpose:** Verify Google Generative AI API connection and model availability

**Run:** `python tests/test_gen.py`

**Tests:**
- API key validation
- Model availability (gemini-2.0-flash-exp, gemini-pro)
- Basic generation test

**Requirements:** GOOGLE_API_KEY in .env

---

#### 7. **test_vector.py** - pgvector Extension Test  
**Purpose:** Verify PostgreSQL pgvector extension is installed

**Run:** `python tests/test_vector.py`

**Tests:**
- Database connection
- pgvector extension creation

**Requirements:** PostgreSQL database credentials in .env

---

#### 8. **verify_rag.py** - RAG System Integration Test
**Purpose:** Verify end-to-end RAG workflow (embed → retrieve → generate)

**Run:** `python tests/verify_rag.py`

**Tests:**
- Embedding service (OpenAI)
- Vector similarity search (pgvector)
- Context retrieval from database
- Answer generation (LLM)

**Requirements:** Django setup, OpenAI API key, populated vector database

---

## Running Tests

### Individual Tests
```bash
cd backend
python tests/test_gap3.py
python tests/test_gap4.py
python tests/test_gap5.py
```

### All Gap Tests (Sequential)
```bash
cd backend
python tests/test_gap3.py && python tests/test_gap4.py && python tests/test_gap5.py
```

### Service Validation Tests
```bash
cd backend
python tests/test_gen.py      # Google Gemini API
python tests/test_vector.py   # pgvector extension
python tests/verify_rag.py    # RAG pipeline
```

---

## Test Requirements

All tests require:
- Python 3.12+
- Django 5.2.9
- PostgreSQL with pgvector
- Environment variables in `.env`:
  - `GOOGLE_API_KEY`
  - `OPENAI_API_KEY`
  - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

Gap tests additionally require:
- Test user account (auto-created if missing)
- Database tables migrated (`python manage.py migrate`)
- For Gap 3: At least one CodingProblem record
- For Gap 4: EmotionEvent, TeachingStrategy tables
- For Gap 5: VisionaryMetric, VisionaryForecast tables

---

## Maintenance Notes

**Keep:**
- All `test_gap*.py` files (validation for project submission)
- `test_sandbox.py`, `test_empath.py` (component validation)

**Can Delete After Initial Setup:**
- `test_gen.py` (one-time API test)
- `test_vector.py` (one-time extension check)
- `verify_rag.py` (one-time RAG pipeline test)

---

## Troubleshooting

**Import Errors:**
- Ensure you're running tests from `backend/` directory
- Check `sys.path` modification at top of test files

**Database Errors:**
- Run `python manage.py migrate` to create tables
- Verify `.env` credentials are correct
- For RAG tests, ensure topics are ingested and approved

**API Errors:**
- Verify API keys in `.env`
- Check internet connection for external APIs
- Google Gemini: Model availability may change, update model names if needed

**Timeout Errors (test_sandbox.py):**
- Test 7 intentionally times out (5+ seconds), this is expected behavior
