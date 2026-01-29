# Walkthrough - Backend Setup and Authentication

## Changes Implemented
### Backend Initialization
- Created Django project `config` and `users` app.
- Configured `settings.py` for PostgreSQL, REST Framework, and CORS.
- Set up environment variables in `.env`.

### Database Integration
- Connected to PostgreSQL database `vaathi`.
- Implemented `CustomUser` model inheriting from `AbstractUser`.
- Successfully ran migrations to create user tables.

### User Authentication
- Implemented `RegisterView` (POST) and `LoginView` (POST).
- Configured URL routing at `/api/register/` and `/api/login/`.

## Verification Results

### Automated Tests
Ran `test_auth_script.py` to verify API endpoints:
```python
Testing Registration...
Registration SUCCESS
Testing Login...
Login SUCCESS
Response: {'id': 1, 'username': 'testuser_v1', ...}
ALL TRIALS PASSED
```

### Manual Verification
- Confirmed server runs at `http://127.0.0.1:8000/`.
- Verified Authentication APIs return correct JSON responses.

## Next Steps
- Proceed to Phase 3: AI & RAG Integration.
