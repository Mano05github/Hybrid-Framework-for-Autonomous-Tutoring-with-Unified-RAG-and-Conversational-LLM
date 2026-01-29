# Vaathiyar - AI-Powered Educational Platform

An intelligent tutoring system leveraging AI for personalized STEM education with multimodal interaction capabilities.

## 🚀 Features

- **Socratic Code Tutor (Gap 3)**: Interactive Python coding environment with progressive hints
- **Voice Assistant (Gap 1)**: Real-time voice interaction with emotion analysis
- **Infinite Canvas (Gap 2)**: Visual learning with handwriting and diagram support
- **Adaptive Learning**: Personalized learning paths based on user performance
- **Real-time Analytics**: Track progress with comprehensive dashboards
- **Session Management**: Seamless learning session tracking and resumption

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 5.2.9 + Django REST Framework
- **WebSockets**: Daphne (ASGI server)
- **AI/ML**: 
  - Gemini 2.0 Flash (LLM)
  - Whisper (Speech-to-Text)
  - Edge TTS (Text-to-Speech)
  - ChromaDB (Vector database for RAG)
- **Code Execution**: RestrictedPython (sandboxed execution)

### Frontend
- **Vanilla JavaScript** (ES6+)
- **HTML5 Canvas** for drawing
- **WebSocket Client** for real-time communication
- **Responsive CSS** with glassmorphism design

## 📦 Installation

### Prerequisites
- Python 3.10+
- pip
- Git

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd V
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file in `backend/` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Collect static files**
```bash
python manage.py collectstatic --noinput
```

7. **Run the server**
```bash
# For HTTP only
python manage.py runserver

# For WebSocket support (voice assistant)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

8. **Access the application**
Open your browser and navigate to: `http://localhost:8000/`

## 📁 Project Structure

```
V/
├── backend/
│   ├── ai_engine/          # AI orchestration and gap implementations
│   ├── config/             # Django settings and configuration
│   ├── core/               # Core models (topics, questions, etc.)
│   ├── learning_session/   # Session management and analytics
│   ├── llm_engine/         # LLM integration (Gemini)
│   ├── rag_system/         # RAG implementation with ChromaDB
│   ├── users/              # User authentication and management
│   ├── static_frontend/    # Frontend HTML/CSS/JS files
│   └── manage.py
└── .gitignore
```

## 🎯 Usage

### Registration & Login
1. Navigate to `/register.html`
2. Create an account (username, email, password)
3. Login at `/login.html`

### Code Editor
1. Go to `/editor.html`
2. Write Python code in the editor
3. Click "Run Code" to execute
4. Click "Get Hint" for Socratic guidance

### Dashboard
- View learning statistics
- Track progress over time
- See recent sessions
- Access different learning modules

### Voice Assistant
1. Navigate to `/voice.html`
2. Click microphone to start voice interaction
3. Ask questions or discuss topics
4. AI responds with voice and text

## 🔧 Development

### Running Tests
```bash
cd backend
python manage.py test
```

### Creating Superuser
```bash
python manage.py createsuperuser
```

### Admin Panel
Access at: `http://localhost:8000/admin/`

## 🌟 Key Features Implementation

### Phase 1: Foundation
- ✅ Frontend-Backend integration
- ✅ Static file serving
- ✅ WebSocket routing

### Phase 2: API Integration
- ✅ Authentication (login/register/logout)
- ✅ Dashboard analytics
- ✅ Code execution
- ✅ Voice assistant WebSocket

### Phase 3: Polish & Fixes
- ✅ Session management endpoints
- ✅ Code execution API
- ✅ Socratic hint system
- ✅ Authentication guards
- ✅ CORS configuration
- ✅ UI polish (logout, user info)

## 🔐 Security

- CSRF protection enabled
- Session-based authentication
- RestrictedPython for code sandboxing
- CORS configured for credentials
- Environment variables for sensitive data

## 📝 API Endpoints

### Authentication
- `POST /api/users/register/` - User registration
- `POST /api/users/login/` - User login
- `POST /api/users/logout/` - User logout
- `GET /api/users/me/` - Get current user

### Sessions
- `POST /api/sessions/start/` - Start learning session
- `POST /api/sessions/{id}/end/` - End session
- `GET /api/sessions/stats/today/` - Today's statistics
- `GET /api/sessions/stats/weekly/` - Weekly statistics

### Coding (Gap 3)
- `POST /api/gaps/coding/execute/` - Execute Python code
- `POST /api/gaps/coding/hint/` - Get Socratic hint

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is for educational purposes.

## 👨‍💻 Author

Manokishore - Final Year Project

## 🙏 Acknowledgments

- Google Gemini AI for LLM capabilities
- Django community for excellent documentation
- OpenAI Whisper for speech recognition
