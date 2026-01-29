# Implementation Details

## 7.1 Module-Wise Explanation

### 7.1.1 Frontend Module (Next.js/React)

**Location**: `frontend/`

**Purpose**: Provides user interface and client-side logic for interacting with the tutoring system

**Key Submodules**:

**app/** - Next.js App Router
- `page.tsx`: Landing page with authentication
- `dashboard/`: User dashboard and course selection
- `chat/`: Main learning interface with chat and code editor
- `progress/`: Learning progress visualization
- `layout.tsx`: Root layout with navigation and theming

**components/** - React Components
- `ChatInterface.tsx`: Message display and input handling
- `MessageBubble.tsx`: Individual message rendering with markdown
- `CodeEditor.tsx`: Monaco editor wrapper for code practice
- `ActiveWhiteboard.tsx`: React-Konva infinite canvas with drawing tools
- `WhiteboardCanvas.tsx`: Basic canvas component for algorithm visualization
- `SessionLayout.tsx`: Learning session layout with canvas and voice controls
- `SidePanel.tsx`: Topic navigation and session history
- `ProgressChart.tsx`: Visualization components for analytics

**hooks/** - Custom React Hooks
- `useWebSocket.ts`: WebSocket connection management with reconnection
- `useAuth.ts`: Authentication state and token management
- `useChat.ts`: Chat history and message sending logic
- `useCodeEditor.ts`: Editor state and syntax highlighting
- `useAudioRecorder.ts`: Voice recording with VAD and audio visualization

**lib/** - Utility Functions
- `api.ts`: Axios instance with interceptors for auth
- `markdown.ts`: Markdown parsing and rendering utilities
- `storage.ts`: LocalStorage helpers for persistence
- `websocket.ts`: WebSocket setup and message protocols

**Technologies**:
- Next.js 16 for routing and SSR
- React 19 for component architecture
- TypeScript for type safety
- Tailwind CSS for styling
- Framer Motion for animations
- React-Konva for interactive canvas
- Web Audio API for voice input/output
- Monaco Editor for code editing
- react-use-websocket for real-time communication

---

### 7.1.2 API Gateway Module (Django)

**Location**: `backend/core/`, `backend/config/`

**Purpose**: Handles HTTP requests, authentication, routing, and middleware

**Key Components**:

**config/settings.py** - Django Configuration
```python
# Key settings
INSTALLED_APPS = [
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'users',
    'ai_engine',
    'rag_system',
    'learning_session',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/hour'
    }
}
```

**config/urls.py** - URL Routing
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/sessions/', include('learning_session.urls')),
    path('api/chat/', include('ai_engine.urls')),
    path('api/content/', include('content.urls')),
]
```

**Middleware Pipeline**:
1. SecurityMiddleware - HTTPS enforcement
2. CorsMiddleware - Cross-origin requests
3. AuthenticationMiddleware - JWT validation
4. ThrottlingMiddleware - Rate limiting
5. LoggingMiddleware - Request/response logging

---

### 7.1.3 AI Engine Module

**Location**: `backend/ai_engine/`

**Purpose**: Implements multi-agent system with supervisor orchestration

**Key Files**:

**agents.py** - Agent Implementations
```python
# Key functions and structure

def get_supervisor_components():
    """Initialize supervisor components (singleton pattern)"""
    global _classifier, _cache, _complexity_analyzer, _dialogue_tracker
    # Lazy initialization
    if _classifier is None:
        _classifier = IntentClassifier(model_path)
    if _cache is None:
        _cache = SemanticCache(redis_url)
    # ... similar for other components
    return _classifier, _cache, _complexity_analyzer, _dialogue_tracker

def supervisor_agent(state: AgentState) -> AgentState:
    """Main supervisor orchestration logic"""
    query = state['query']
    
    # 1. Check semantic cache
    cached = cache.get(query)
    if cached:
        state['response'] = cached
        return state
    
    # 2. Classify intent
    intent_result = classifier.classify(query)
    state['intent'] = intent_result['primary_intent']
    
    # 3. Analyze complexity
    complexity = complexity_analyzer.analyze(query)
    state['complexity'] = complexity
    
    # 4. Route to appropriate agent
    if intent == 'teach':
        state = teacher_agent(state)
    elif intent == 'examine':
        state = examiner_agent(state)
    elif intent == 'analyze':
        state = analyst_agent(state)
    elif intent == 'guide':
        state = visionary_agent(state)
    elif intent == 'empath':
        state = empath_agent(state)
    
    # 5. Update cache
    cache.set(query, state['response'])
    
    # 6. Update dialogue state
    dialogue_tracker.update(state)
    
    return state

def teacher_agent(state: AgentState) -> AgentState:
    """Teacher agent with RAG integration"""
    query = state['query']
    complexity = state['complexity']
    
    # Select RAG strategy based on complexity
    if complexity <= 3:
        rag = get_baseline_rag(topic_id)
    elif complexity <= 6:
        rag = get_adaptive_rag(intent=state['intent'], topic_id)
    else:
        rag = get_omni_rag(topic_id)
    
    # Retrieve context
    docs = rag.get_relevant_documents(query)
    context = format_context(docs)
    
    # Construct prompt
    prompt = construct_teacher_prompt(query, context, state)
    
    # Call LLM
    llm = LLMFactory.get_llm(provider='openai', model='gpt-4')
    response = llm.generate(prompt)
    
    state['response'] = response
    state['sources'] = [doc.metadata for doc in docs]
    
    return state

def empath_agent(state: AgentState) -> AgentState:
    """Empath agent for emotional support and encouragement"""
    query = state['query']
    user_emotion = state.get('user_emotion', 'neutral')
    
    # Construct empathetic prompt
    prompt = f"""You are a supportive and empathetic tutor. The student is feeling {user_emotion}.
    
Student's message: {query}

Provide warm, encouraging support that:
1. Acknowledges their feelings
2. Offers reassurance and motivation
3. Suggests constructive approaches to overcome challenges
4. Reminds them that learning difficulties are normal and temporary

Be genuine, supportive, and personalized. Use a warm, conversational tone."""
    
    # Call LLM with high temperature for warmth
    llm = LLMFactory.get_llm(provider='openai', model='gpt-4', temperature=0.8)
    response = llm.generate(prompt)
    
    state['response'] = response
    state['agent_type'] = 'empath'
    
    return state
```

**supervisor/classifier.py** - SetFit Intent Classifier
```python
class IntentClassifier:
    """Multi-label intent classification using SetFit"""
    
    def __init__(self, model_path: Optional[str] = None):
        if model_path and Path(model_path).exists():
            self.model = SetFitModel.from_pretrained(model_path)
        else:
            # Train new model
            self.model = self._train_model()
    
    def classify(self, query: str) -> Dict:
        """Classify query intent"""
        # Get predictions
        probs = self.model.predict_proba([query])[0]
        
        # Map to intent labels
        intents = ['teach', 'practice', 'examine', 'analyze', 'guide', 'empath']
        intent_scores = dict(zip(intents, probs))
        
        # Primary intent: highest score above threshold
        primary = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[primary]
        
        # Secondary intents: scores above secondary threshold (0.3)
        secondary = [k for k, v in intent_scores.items() 
                    if v > 0.3 and k != primary]
        
        return {
            'primary_intent': primary,
            'confidence': confidence,
            'secondary_intents': secondary,
            'all_scores': intent_scores
        }
```

**supervisor/cache.py** - Semantic Cache
```python
class SemanticCache:
    """Redis-backed semantic cache with vector similarity"""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.threshold = 0.92  # High similarity threshold
    
    def get(self, query: str) -> Optional[str]:
        """Retrieve cached response if similar query exists"""
        query_emb = self.embedder.encode(query)
        
        # Retrieve all cached query embeddings
        cached_keys = self.redis.keys('cache:*')
        
        for key in cached_keys:
            cached_emb = np.frombuffer(
                self.redis.hget(key, 'embedding'), dtype=np.float32
            )
            similarity = cosine_similarity(query_emb, cached_emb)
            
            if similarity > self.threshold:
                # Cache hit
                return self.redis.hget(key, 'response').decode()
        
        return None  # Cache miss
    
    def set(self, query: str, response: str, ttl: int = 3600):
        """Store query-response pair with embedding"""
        query_emb = self.embedder.encode(query)
        key = f"cache:{hash(query)}"
        
        self.redis.hset(key, mapping={
            'query': query,
            'response': response,
            'embedding': query_emb.tobytes()
        })
        self.redis.expire(key, ttl)
```

**supervisor/complexity.py** - Complexity Analyzer
```python
class ComplexityAnalyzer:
    """Heuristic-based query complexity scoring"""
    
    def analyze(self, query: str) -> int:
        """Compute complexity score (1-10)"""
        score = 0
        
        # Length factor
        word_count = len(query.split())
        if word_count > 50:
            score += 3
        elif word_count > 20:
            score += 2
        elif word_count > 10:
            score += 1
        
        # Multi-part questions
        question_marks = query.count('?')
        score += min(question_marks, 2)
        
        # Technical terms (simple keyword matching)
        technical_terms = ['algorithm', 'complexity', 'implement', 
                          'optimize', 'analyze', 'compare']
        score += sum(1 for term in technical_terms if term in query.lower())
        
        # Code presence
        if '```' in query or 'def ' in query or 'class ' in query:
            score += 2
        
        # Cap at 10
        return min(score, 10)
```

**supervisor/dialogue.py** - Dialogue State Tracker
```python
class DialogueStateTracker:
    """
    Context-aware conversation tracking with coreference resolution.
    
    Features:
    1. Coreference Resolution: "it", "that" -> actual concept
    2. Topic Tracking: Maintains conversation topic across turns
    3. Entity Memory: Remembers CS concepts/algorithms mentioned
    4. Follow-up Detection: Identifies continuation queries
    
    Example:
        Turn 1: "Explain binary search"
        Turn 2: "Give me practice problems on it"
        Resolved: "Give me practice problems on binary search"
    """
    
    PRONOUNS = {'it', 'that', 'this', 'them', 'these', 'those'}
    FOLLOWUP_PHRASES = [
        'explain more', 'tell me more', 'continue',
        'what about', 'how about', 'also', 'on that'
    ]
    
    def __init__(self, max_history: int = 50):
        self.sessions = {}  # session_id -> DialogueState
        self.nlp = spacy.load("en_core_web_sm")
    
    def track_turn(self, user_id: str, session_id: str, 
                   query: str, intent: str, response: str):
        """Add turn to dialogue history with entity extraction"""
        # Parse query
        doc = self.nlp(query.lower())
        
        # Extract CS entities (algorithms, data structures)
        entities = self._extract_entities(doc)
        topic = self._detect_topic(doc)
        
        # Update state
        state = self.sessions.get(session_id)
        state.current_topic = topic
        state.mentioned_entities.update(entities)
        
        # Store turn
        turn = DialogueTurn(
            turn_id=len(state.turns) + 1,
            query=query,
            intent=intent,
            response=response,
            entities=entities,
            topic=topic
        )
        state.turns.append(turn)
    
    def resolve_context(self, query: str, session_id: str):
        """Resolve pronouns and add context"""
        state = self.sessions.get(session_id)
        doc = self.nlp(query.lower())
        
        # Check for pronouns
        has_pronoun = any(token.text in self.PRONOUNS for token in doc)
        
        if has_pronoun and state.current_topic:
            # Replace pronoun with actual topic
            resolved_query = self._replace_pronouns(query, state.current_topic)
            return resolved_query, {'resolved': True, 'topic': state.current_topic}
        
        # Check for follow-up indicators
        is_followup = any(p in query.lower() for p in self.FOLLOWUP_PHRASES)
        if is_followup:
            return query, {'is_followup': True, 'topic': state.current_topic}
        
        return query, {}
    
    def _replace_pronouns(self, query: str, topic: str) -> str:
        """Replace pronouns with topic name"""
        for pronoun in self.PRONOUNS:
            query = query.replace(f" {pronoun} ", f" {topic} ")
            query = query.replace(f" {pronoun.capitalize()} ", f" {topic} ")
        return query
    
    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract CS concepts using spaCy NER"""
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        return entities
    
    def _detect_topic(self, doc) -> Optional[str]:
        """Detect CS topic from query"""
        topics = {
            'data_structures': ['array', 'list', 'stack', 'queue', 'tree', 'graph'],
            'algorithms': ['sort', 'search', 'recursion', 'dynamic programming'],
            'complexity': ['big o', 'time complexity', 'space complexity']
        }
        
        for topic, keywords in topics.items():
            if any(kw in doc.text for kw in keywords):
                return topic
        return None
```

---

### 7.1.4 RAG System Module

**Location**: `backend/rag_system/`

**Purpose**: Implements three RAG strategies with hybrid retrieval

**Key Files**:

**__init__.py** - RAG Factory
```python
def get_baseline_rag(collection_name: str, top_k: int = 5):
    """Simple vector search RAG"""
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    return vectorstore.as_retriever(search_kwargs={'k': top_k})

def get_adaptive_rag(intent: str, collection_name: str, user_context: dict):
    """Intent-aware RAG with metadata filtering"""
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(...)
    
    # Configure based on intent
    if intent == 'teach':
        top_k = 8
        metadata_filter = {'content_type': {'$in': ['theory', 'examples']}}
    elif intent == 'practice':
        top_k = 5
        metadata_filter = {'content_type': 'exercises'}
    # ... other intents
    
    return vectorstore.as_retriever(
        search_kwargs={'k': top_k, 'filter': metadata_filter}
    )

def get_omni_rag(collection_name: str, top_k: int = 5):
    """Full hybrid RAG with reranking"""
    return OmniRAGRetriever(collection_name, top_k)
```

**hybrid_retriever.py** - Omni-RAG Implementation
```python
class OmniRAGRetriever:
    """Hybrid retriever with vector + BM25 + reranking"""
    
    def __init__(self, collection_name: str, top_k: int = 5):
        self.collection_name = collection_name
        self.top_k = top_k
        
        # Initialize components
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vectorstore = Chroma(...)
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Load BM25 index
        self.bm25_retriever = self._init_bm25()
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Main retrieval pipeline"""
        # Stage 1: Dual retrieval
        vector_docs = self._vector_search(query, k=20)
        bm25_docs = self._bm25_search(query, k=20)
        
        # Stage 2: Reciprocal rank fusion
        fused_docs = self._reciprocal_rank_fusion(
            [vector_docs, bm25_docs]
        )
        
        # Stage 3: Cross-encoder reranking
        reranked_docs = self._rerank(query, fused_docs)
        
        # Stage 4: Context compression
        compressed_docs = self._compress_context(reranked_docs[:self.top_k])
        
        return compressed_docs
    
    def _reciprocal_rank_fusion(self, rankings: List, k: int = 60):
        """Combine rankings using RRF"""
        fused_scores = {}
        for rank_list in rankings:
            for rank, doc in enumerate(rank_list, 1):
                doc_id = doc.metadata['id']
                score = 1 / (k + rank)
                fused_scores[doc_id] = fused_scores.get(doc_id, 0) + score
        
        # Sort and return top-20
        sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [self._get_doc_by_id(doc_id) for doc_id, _ in sorted_docs[:20]]
    
    def _rerank(self, query: str, docs: List[Document]):
        """Cross-encoder reranking"""
        pairs = [[query, doc.page_content] for doc in docs]
        scores = self.cross_encoder.predict(pairs)
        
        # Sort by relevance score
        scored_docs = list(zip(docs, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs]
```

---

### 7.1.5 LLM Engine Module

**Location**: `backend/llm_engine/`

**Purpose**: Abstracts LLM provider interactions

**factory.py** - LLM Factory Pattern
```python
class LLMFactory:
    """Factory for creating LLM instances"""
    
    @staticmethod
    def get_llm(provider: str, model: str, **kwargs):
        if provider == 'openai':
            return OpenAILLM(model, **kwargs)
        elif provider == 'gemini':
            return GeminiLLM(model, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

class OpenAILLM:
    """OpenAI LLM wrapper"""
    
    def __init__(self, model: str, temperature: float = 0.5):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model
        self.temperature = temperature
    
    def generate(self, prompt: str, max_tokens: int = 1500) -> str:
        """Generate response with retry logic"""
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=self.temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

---

### 7.1.6 Learning Session Module

**Location**: `backend/learning_session/`

**Purpose**: Manages user sessions and conversation history

**models.py** - Data Models
```python
class Session(models.Model):
    """Learning session"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    state = models.JSONField(default=dict)  # Dialogue state

class Message(models.Model):
    """Chat message"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    agent_type = models.CharField(max_length=50, null=True)  # Which agent responded
    metadata = models.JSONField(default=dict)  # Intent, complexity, sources, etc.
```

**views.py** - API Endpoints

---

### 7.1.7 Audio & Speech Services

**Location**: `backend/learning_session/stt_service.py`, `backend/learning_session/emotion_service.py`, `backend/learning_session/tts_service.py`

**Purpose**: Handle complete voice interaction loop - speech-to-text, emotion recognition, and text-to-speech generation

**stt_service.py** - Speech-to-Text Transcription
```python
import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

class STTService:
    """Speech-to-text transcription using Google Web Speech API"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        logger.info("STT Service Initialized (Google Web Speech API)")
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes audio file to text using Google Speech Recognition.
        
        Args:
            audio_path: Path to WAV audio file
            
        Returns:
            Transcribed text string, or None if recognition fails
        """
        try:
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
            
            # Use Google Web Speech API (Free, internet connection required)
            text = self.recognizer.recognize_google(audio_data)
            logger.info(f"STT Transcription: {text}")
            return text
            
        except sr.UnknownValueError:
            # Speech not understood
            logger.warning("STT: Speech not recognized")
            return None
            
        except sr.RequestError as e:
            # API request failed
            logger.error(f"STT Service Error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"STT Unexpected Error: {e}")
            return None
```

**emotion_service.py** - Speech Emotion Recognition
```python
import librosa
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification

class EmotionService:
    """Speech emotion recognition using acoustic features"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.is_ready = False
        
    def load_model(self):
        """Lazy load Wav2Vec2 emotion model"""
        if self.is_ready:
            return
            
        try:
            logger.info("Loading Emotion Recognition Model (Wav2Vec2)...")
            # Placeholder for actual model - can be replaced with fine-tuned model
            self.processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(
                "superb/wav2vec2-base-superb-er"  # Emotion recognition
            )
            self.is_ready = True
            logger.info("Emotion Model Loaded Successfully")
        except Exception as e:
            logger.error(f"Failed to load Emotion Model: {e}")
    
    def analyze_audio(self, audio_path: str) -> str:
        """
        Analyzes audio file and returns emotion label.
        
        Returns one of: neutral, calm, happy, sad, angry, fearful, surprised
        """
        try:
            # 1. Load audio with librosa
            y, sr = librosa.load(audio_path, sr=16000, duration=3.0)
            
            # 2. Extract MFCC features (40 coefficients)
            mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
            
            # 3. Extract Mel-spectrogram for CNN input
            mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            # 4. Model prediction (if loaded)
            if self.is_ready:
                inputs = self.processor(y, sampling_rate=16000, return_tensors="pt")
                logits = self.model(**inputs).logits
                predicted_id = torch.argmax(logits, dim=-1).item()
                
                # Map to emotion labels
                emotion_labels = ["neutral", "calm", "happy", "sad", "angry", "fearful", "surprised"]
                detected_emotion = emotion_labels[predicted_id % len(emotion_labels)]
                
                return detected_emotion
            else:
                # Fallback: basic heuristic based on pitch/energy
                pitch = librosa.feature.zero_crossing_rate(y)
                energy = np.sqrt(np.mean(y**2))
                
                if energy < 0.01:
                    return "calm"
                elif energy > 0.05 and np.mean(pitch) > 0.1:
                    return "frustrated"
                else:
                    return "neutral"
                    
        except Exception as e:
            logger.error(f"Emotion Analysis Failed: {e}")
            return "neutral"
    
    def adapt_response_tone(self, emotion: str, base_prompt: str) -> str:
        """Modify system prompt based on detected emotion"""
        if emotion in ["frustrated", "angry"]:
            return base_prompt + "\n\nThe student sounds frustrated. Be extra patient and encouraging. Break down concepts into smaller steps."
        elif emotion in ["sad", "fearful"]:
            return base_prompt + "\n\nThe student seems uncertain. Provide reassurance and confidence-building support."
        elif emotion == "happy":
            return base_prompt + "\n\nThe student is engaged and positive. Maintain enthusiasm and challenge them appropriately."
        else:
            return base_prompt
```

**tts_service.py** - Text-to-Speech Generation
```python
import edge_tts
import asyncio
import logging

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-speech using Microsoft Edge TTS"""
    
    def __init__(self, voice="en-US-ChristopherNeural"):
        self.voice = voice  # Professional male voice
        # Alternative voices:
        # - en-US-AriaNeural (female, conversational)
        # - en-GB-SoniaNeural (British female, formal)
        # - en-US-GuyNeural (male, news broadcaster)
        logger.info(f"TTS Service initialized with voice: {self.voice}")
    
    async def generate_audio(self, text: str) -> bytes:
        """
        Generates MP3 audio bytes from text.
        
        Args:
            text: Text to synthesize
            
        Returns:
            MP3 audio data as bytes
        """
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            audio_data = b""
            
            # Stream audio chunks
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            logger.info(f"Generated TTS Audio: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS Generation Failed: {e}")
            return None
    
    def set_voice(self, voice: str):
        """Change TTS voice"""
        self.voice = voice
        logger.info(f"TTS voice changed to: {voice}")
```

**consumers.py** - WebSocket Consumer for Audio
```python
import json
import base64
import tempfile
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .stt_service import STTService
from .emotion_service import EmotionService
from .tts_service import TTSService

class SessionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time session communication"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stt_service = STTService()
        self.emotion_service = EmotionService()
        self.tts_service = TTSService()
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'session_{self.session_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages - text or binary audio"""
        
        if bytes_data:
            # Audio input received
            await self._handle_audio_input(bytes_data)
        elif text_data:
            # Text input received
            data = json.loads(text_data)
            await self._handle_text_input(data)
    
    async def _handle_audio_input(self, audio_bytes):
        """Process audio input for STT transcription and emotion recognition"""
        try:
            # 1. Save audio bytes to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name
            
            # 2. Parallel processing: STT + Emotion (both analyze same audio)
            # Transcribe speech to text
            user_text = await sync_to_async(self.stt_service.transcribe)(temp_path)
            
            # Analyze emotion from voice tone
            emotion = await sync_to_async(self.emotion_service.analyze_audio)(temp_path)
            
            # 3. Cleanup temporary file
            os.remove(temp_path)
            
            # 4. Send emotion update to frontend
            await self.send(text_data=json.dumps({
                'type': 'emotion_detected',
                'emotion': emotion,
                'timestamp': datetime.now().isoformat()
            }))
            
            # 5. Process transcribed text if recognition successful
            if user_text:
                print(f"User said: {user_text} [Emotion: {emotion}]")
                
                # Call supervisor agent with transcribed text and emotion context
                response_text = await self._process_query(user_text, emotion)
                
                # Send text response (and optionally audio)
                await self.send(text_data=json.dumps({
                    'type': 'response',
                    'text': response_text,
                    'user_query': user_text,
                    'emotion': emotion
                }))
            else:
                # Speech not recognized
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Could not understand speech. Please try again.'
                }))
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error processing audio input'
            }))
    
    async def _handle_text_input(self, data):
        """Process text query and generate response with optional TTS"""
        query = data.get('query')
        enable_tts = data.get('enable_tts', False)
        
        # Process query through supervisor agent
        response_text = await self._process_query(query, emotion='neutral')
        
        # Generate audio if requested
        if enable_tts:
            audio_bytes = await self.tts_service.generate_audio(response_text)
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            await self.send(text_data=json.dumps({
                'type': 'response',
                'text': response_text,
                'audio': audio_base64,
                'audio_format': 'mp3'
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'response',
                'text': response_text
            }))
    
    async def _process_query(self, query: str, emotion: str) -> str:
        """Process query through AI orchestrator with emotion context"""
        # This would call your supervisor agent
        # ... supervisor processing logic ...
        return "AI response here"
```

**views.py** - API Endpoints
```python
class ChatView(APIView):
    """Handle chat interactions"""
    
    def post(self, request):
        """Process user message"""
        query = request.data.get('query')
        session_id = request.data.get('session_id')
        
        # Load or create session
        session = Session.objects.get_or_create(
            id=session_id,
            user=request.user,
            defaults={'status': 'active'}
        )[0]
        
        # Save user message
        Message.objects.create(
            session=session,
            role='user',
            content=query
        )
        
        # Prepare agent state
        state = AgentState(
            query=query,
            user_id=str(request.user.id),
            session_id=str(session_id),
            history=get_conversation_history(session)
        )
        
        # Call supervisor
        result_state = supervisor_agent(state)
        
        # Save assistant response
        Message.objects.create(
            session=session,
            role='assistant',
            content=result_state['response'],
            agent_type=result_state.get('agent_type'),
            metadata={
                'intent': result_state.get('intent'),
                'complexity': result_state.get('complexity'),
                'sources': result_state.get('sources', [])
            }
        )
        
        return Response({
            'response': result_state['response'],
            'metadata': result_state.get('metadata', {})
        })
```

---

## 7.2 Folder Structure

```
V/
├── backend/
│   ├── ai_engine/                # Multi-agent system
│   │   ├── agents.py            # Agent implementations
│   │   ├── state.py             # Shared state definitions
│   │   ├── supervisor/          # Supervisor components
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py    # Intent classification
│   │   │   ├── cache.py         # Semantic cache
│   │   │   ├── complexity.py    # Complexity analysis
│   │   │   └── dialogue.py      # Dialogue tracking
│   │   ├── models/              # ML models storage
│   │   │   └── setfit_intent_classifier/
│   │   └── migrations/
│   ├── rag_system/              # RAG implementation
│   │   ├── __init__.py          # RAG factory functions
│   │   ├── hybrid_retriever.py  # Omni-RAG implementation
│   │   └── storage/             # ChromaDB persistence
│   ├── llm_engine/              # LLM integration
│   │   ├── __init__.py
│   │   └── factory.py           # LLM factory
│   ├── learning_session/        # Session management
│   │   ├── models.py            # Session/Message models
│   │   ├── views.py             # API endpoints
│   │   ├── urls.py
│   │   └── serializers.py
│   ├── users/                   # Authentication
│   │   ├── models.py            # User model
│   │   ├── views.py             # Auth endpoints
│   │   └── serializers.py
│   ├── core/                    # Core app (topics, lessons)
│   │   ├── models.py
│   │   ├── views.py
│   │   └── admin.py
│   ├── config/                  # Django settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js pages
│   │   ├── page.tsx            # Landing page
│   │   ├── dashboard/
│   │   ├── chat/
│   │   └── layout.tsx
│   ├── components/              # React components
│   │   ├── ChatInterface.tsx
│   │   ├── CodeEditor.tsx
│   │   └── ...
│   ├── hooks/                   # Custom hooks
│   │   ├── useWebSocket.ts
│   │   ├── useAuth.ts
│   │   └── ...
│   ├── lib/                     # Utilities
│   │   ├── api.ts
│   │   ├── markdown.ts
│   │   └── ...
│   ├── public/                  # Static assets
│   ├── package.json
│   └── next.config.ts
└── brain/                       # Vector storage
    └── {topic-id}/              # Per-topic collections
        └── chroma.sqlite3
```

## 7.3 Key Functions / Classes

### Backend
- `supervisor_agent()`: Main orchestration logic
- `teacher_agent()`: Teaching response generation
- `IntentClassifier`: SetFit-based classification
- `SemanticCache`: Redis-backed caching
- `OmniRAGRetriever`: Hybrid search implementation
- `LLMFactory`: LLM provider abstraction
- `Session`, `Message`: Database models

### Frontend
- `ChatInterface`: Main chat UI component
- `useWebSocket()`: WebSocket connection management
- `useAuth()`: Authentication state handling
- `CodeEditor`: Monaco editor wrapper

## 7.4 Data Handling Approach

**Request Flow**:
1. Frontend sends request with JWT token
2. API Gateway validates authentication
3. Request routed to appropriate view
4. View loads session and conversation history
5. Supervisor processes with multi-agent system
6. RAG retrieves relevant context
7. LLM generates response
8. Response saved to database
9. Response streamed back to frontend

**Data Persistence**:
- **PostgreSQL**: Users, sessions, messages, progress
- **ChromaDB**: Document embeddings per topic
- **Redis**: Semantic cache, session data
- **File System**: ML models, static content

**State Management**:
- Frontend: React Context API for global state
- Backend: AgentState dataclass passed between agents
- Database: JSONField for flexible state storage

This modular architecture enables independent development, testing, and scaling of components while maintaining clear interfaces and separation of concerns.
