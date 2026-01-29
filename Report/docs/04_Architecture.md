# Architecture

## 4.1 Detailed System Architecture

The system architecture follows a microservices-inspired design with clear separation between presentation, business logic, and data layers. The architecture emphasizes modularity, enabling independent scaling and maintenance of components.

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOBILE[Mobile Browser]
    end
    
    subgraph "Presentation Layer - Next.js Frontend"
        UI[React UI Components]
        STATE[State Management]
        WS_CLIENT[WebSocket Client]
        HTTP_CLIENT[HTTP Client]
    end
    
    subgraph "API Gateway Layer - Django"
        AUTH[JWT Authentication]
        ROUTER[URL Router]
        MIDDLEWARE[Middleware Pipeline]
        VIEWS[REST API Views]
    end
    
    subgraph "Business Logic Layer"
        subgraph "Supervisor System"
            SUP[Supervisor Orchestrator]
            INTENT[SetFit Intent Classifier]
            CACHE_MGR[Semantic Cache Manager]
            COMPLEX[Complexity Analyzer]
            DIALOGUE[Dialogue State Tracker]
        end
        
        subgraph "Agent Layer"
            TEACHER[Teacher Agent]
            ANALYST[Analyst Agent]
            EXAMINER[Examiner Agent]
            CODER[Socratic Coder Agent - Gap 3]
            EMPATH[Empath Agent - Gap 4]
            VISIONARY[Visionary Agent - Gap 5]
        end
        
        subgraph "Voice Assistant System - Gap 1"
            WAKE[Wake Word Detection - Bi-LSTM]
            STT[Speech-to-Text - CNN-LSTM + CTC]
            NLU[NLU - BERT Multi-Task]
            TTS[Text-to-Speech - FastSpeech2 + HiFi-GAN]
            VOICE_CORE[Voice Core Orchestrator]
        end
        
        subgraph "Gap 3: Socratic Coder"
            SANDBOX[RestrictedPython Sandbox]
            HINT_ENGINE[5-Level Hint System]
            CODE_VALIDATOR[Test Case Validator]
            STRUGGLE_DETECTOR[Struggle Detection]
        end
        
        subgraph "Gap 4: Adaptive Empath"
            SENTIMENT[Transformer Sentiment - DistilBERT]
            MULTI_SIGNAL[Multi-Signal Fusion]
            INTERVENTION[4 Intervention Strategies]
            TOPIC_GRAPH[Topic Graph Traversal]
        end
        
        subgraph "Gap 5: Always-On Visionary"
            TELEMETRY[Session Telemetry Calculator]
            TREND_ANALYZER[Velocity Trend Analysis]
            STRUGGLE_PREDICTOR[Struggle Prediction]
            STRATEGIC_INSIGHT[Strategic Recommendations]
        end
        
        subgraph "RAG Engine"
            RAG_FACTORY[RAG Strategy Factory]
            BASELINE[Baseline RAG]
            ADAPTIVE[Adaptive RAG]
            OMNI[Omni-RAG]
            
            subgraph "Omni-RAG Pipeline"
                EMBEDDER[Embedding Model]
                VEC_SEARCH[Vector Retriever]
                BM25_SEARCH[BM25 Retriever]
                RRF[Reciprocal Rank Fusion]
                RERANKER[Cross-Encoder Reranker]
                COMPRESSOR[Context Compressor]
            end
        end
        
        subgraph "LLM Integration"
            LLM_FACTORY[LLM Factory]
            OPENAI_CLIENT[OpenAI Client]
            GEMINI_CLIENT[Gemini Client]
        end
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL + pgvector)]
        CHROMADB[(ChromaDB Vector Store)]
        REDIS[(Redis Cache)]
        FILESYSTEM[File System - Brain Storage]
    end
    
    subgraph "External Services"
        OPENAI_API[OpenAI API]
        GEMINI_API[Google Gemini API]
    end
    
    WEB --> UI
    MOBILE --> UI
    UI --> STATE
    STATE --> WS_CLIENT
    STATE --> HTTP_CLIENT
    
    WS_CLIENT --> ROUTER
    HTTP_CLIENT --> ROUTER
    
    ROUTER --> AUTH
    AUTH --> MIDDLEWARE
    MIDDLEWARE --> VIEWS
    
    VIEWS --> SUP
    
    SUP --> INTENT
    SUP --> CACHE_MGR
    SUP --> COMPLEX
    SUP --> DIALOGUE
    
    CACHE_MGR --> REDIS
    
    SUP --> TEACHER
    SUP --> ANALYST
    SUP --> EXAMINER
    SUP --> VISIONARY
    
    TEACHER --> RAG_FACTORY
    RAG_FACTORY --> BASELINE
    RAG_FACTORY --> ADAPTIVE
    RAG_FACTORY --> OMNI
    
    OMNI --> EMBEDDER
    EMBEDDER --> VEC_SEARCH
    EMBEDDER --> BM25_SEARCH
    VEC_SEARCH --> RRF
    BM25_SEARCH --> RRF
    RRF --> RERANKER
    RERANKER --> COMPRESSOR
    
    VEC_SEARCH --> CHROMADB
    BASELINE --> CHROMADB
    ADAPTIVE --> CHROMADB
    
    CHROMADB --> FILESYSTEM
    
    TEACHER --> LLM_FACTORY
    ANALYST --> LLM_FACTORY
    EXAMINER --> LLM_FACTORY
    VISIONARY --> LLM_FACTORY
    
    LLM_FACTORY --> OPENAI_CLIENT
    LLM_FACTORY --> GEMINI_CLIENT
    
    OPENAI_CLIENT --> OPENAI_API
    GEMINI_CLIENT --> GEMINI_API
    
    VIEWS --> POSTGRES
    DIALOGUE --> POSTGRES
```

## 4.1.1 Multimodal Interaction Architecture

The system supports three input modalities: text, voice, and visual canvas. The following diagram shows the complete multimodal data flow:

```mermaid
graph TB
    subgraph "Frontend Multimodal Input"
        TEXT_INPUT[Text Chat Input]
        VOICE_INPUT[Voice Recording]
        CANVAS_INPUT[Interactive Canvas]
        
        VOICE_INPUT --> VAD[Voice Activity Detection]
        VAD --> AUDIO_BLOB[Audio Blob WAV]
        
        CANVAS_INPUT --> KONVA[React-Konva Engine]
        KONVA --> CANVAS_STATE[Canvas State JSON]
        KONVA --> CANVAS_SNAPSHOT[Canvas Snapshot PNG]
    end
    
    subgraph "WebSocket Communication"
        WS[Django Channels WebSocket]
        WS_CONSUMER[Session Consumer]
    end
    
    subgraph "Audio Processing Pipeline"
        AUDIO_BLOB --> WS
        WS --> STT_SVC[Speech-to-Text Service]
        WS --> EMOTION_SVC[Emotion Recognition Service]
        
        STT_SVC --> SPEECH_REC[SpeechRecognition Library]
        SPEECH_REC --> TRANSCRIBED_TEXT[Transcribed Text]
        
        EMOTION_SVC --> LIBROSA[librosa Feature Extractor]
        LIBROSA --> MFCC[MFCC Features]
        LIBROSA --> MEL[Mel-Spectrogram]
        MFCC --> CNN_LSTM[CNN-LSTM Model]
        MEL --> CNN_LSTM
        CNN_LSTM --> EMOTION_STATE[Emotion: calm/frustrated/confused]
    end
    
    subgraph "Canvas Processing Pipeline"
        CANVAS_SNAPSHOT --> WS
        WS --> VISION_AGENT[Visionary Agent]
        VISION_AGENT --> VISUAL_LLM[GPT-4 Vision/Gemini Pro Vision]
        VISUAL_LLM --> DIAGRAM_ANALYSIS[Diagram Validation]
    end
    
    subgraph "Unified Context Builder"
        TEXT_INPUT --> CONTEXT[Session Context]
        TRANSCRIBED_TEXT --> CONTEXT
        EMOTION_STATE --> CONTEXT
        DIAGRAM_ANALYSIS --> CONTEXT
        CONTEXT --> SUPERVISOR[Supervisor Agent]
    end
    
    subgraph "Response Generation"
        SUPERVISOR --> RESPONSE_TEXT[Text Response]
        RESPONSE_TEXT --> TTS_SVC[Text-to-Speech Service]
        TTS_SVC --> EDGE_TTS[Edge TTS Engine]
        EDGE_TTS --> AUDIO_RESPONSE[Audio MP3]
        AUDIO_RESPONSE --> WS
        RESPONSE_TEXT --> WS
    end
    
    WS --> WS_CLIENT[Frontend WebSocket Client]
    WS_CLIENT --> TEXT_OUTPUT[Display Text Response]
    WS_CLIENT --> AUDIO_PLAYER[Audio Playback]
```

**Key Multimodal Features:**

1. **Complete Voice Interaction Loop**
   - **Speech-to-Text (STT)**: Google Web Speech API converts student speech to text
   - **Emotion Recognition**: CNN-LSTM analyzes tone, pitch, and rhythm in parallel
   - **Text-to-Speech (TTS)**: Edge TTS generates natural voice responses
   - Enables fully hands-free voice-based tutoring sessions

2. **Voice Emotion Recognition**
   - Real-time audio capture via Web Audio API
   - Voice Activity Detection triggers recording automatically
   - CNN-LSTM model analyzes tone, pitch, and rhythm
   - Detects emotional states: neutral, calm, happy, frustrated, confused, angry
   - Emotion state influences AI response tone and scaffolding level

3. **Interactive Canvas**
   - Infinite pan/zoom grid for algorithm visualization
   - Drawing tools: pen, shapes (circles, rectangles), text, eraser
   - Specialized node creation for data structures (BST, graphs, linked lists)
   - History management (undo/redo) with state persistence
   - Real-time canvas snapshot for AI vision analysis

4. **Canvas-AI Co-Creation**
   - Student draws algorithm/diagram on canvas
   - System captures canvas state as JSON + PNG snapshot
   - Visionary agent analyzes drawing correctness
   - AI provides visual feedback and corrections
   - Supports collaborative debugging of visual concepts

## 4.2 Data Flow Diagram

### 4.2.1 User Query Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API Gateway
    participant Supervisor
    participant Cache
    participant Intent Classifier
    participant Teacher Agent
    participant RAG System
    participant Vector Store
    participant LLM
    
    User->>Frontend: Submit Query
    Frontend->>API Gateway: HTTP/WebSocket Request
    API Gateway->>API Gateway: Authenticate User
    API Gateway->>Supervisor: Forward Query + Context
    
    Supervisor->>Cache: Check Semantic Cache
    alt Cache Hit
        Cache-->>Supervisor: Return Cached Response
        Supervisor-->>Frontend: Response
        Frontend-->>User: Display Response
    else Cache Miss
        Supervisor->>Intent Classifier: Classify Query Intent
        Intent Classifier-->>Supervisor: Intent: "teach", Complexity: 7
        
        Supervisor->>Teacher Agent: Route Query
        Teacher Agent->>RAG System: Request Context (Omni-RAG)
        
        RAG System->>Vector Store: Vector Search
        RAG System->>Vector Store: BM25 Keyword Search
        Vector Store-->>RAG System: Candidate Documents
        
        RAG System->>RAG System: Reciprocal Rank Fusion
        RAG System->>RAG System: Cross-Encoder Reranking
        RAG System-->>Teacher Agent: Top-5 Relevant Contexts
        
        Teacher Agent->>Teacher Agent: Construct Prompt
        Teacher Agent->>LLM: Generate Response
        LLM-->>Teacher Agent: AI Response
        
        Teacher Agent-->>Supervisor: Formatted Response
        Supervisor->>Cache: Store in Semantic Cache
        Supervisor-->>API Gateway: Response + Metadata
        API Gateway-->>Frontend: JSON Response
        Frontend-->>User: Display Response
    end
```

### 4.2.2 Knowledge Ingestion Flow

```mermaid
flowchart TD
    START[PDF Upload] --> EXTRACT[Text Extraction]
    EXTRACT --> SPLIT[Document Chunking]
    SPLIT --> META[Metadata Extraction]
    META --> EMBED[Generate Embeddings]
    EMBED --> STORE_VEC[Store in ChromaDB]
    EMBED --> STORE_DB[Store Metadata in PostgreSQL]
    STORE_VEC --> INDEX[Build Vector Index]
    STORE_DB --> COMPLETE[Ingestion Complete]
    INDEX --> COMPLETE
```

### 4.2.3 Multi-Agent Collaboration Flow

```mermaid
sequenceDiagram
    participant User
    participant Supervisor
    participant Teacher
    participant Examiner
    participant Analyst
    
    User->>Supervisor: "Explain binary search"
    Supervisor->>Teacher: Route to Teacher
    Teacher-->>User: Detailed Explanation
    
    User->>Supervisor: "Give me a practice problem"
    Supervisor->>Teacher: Route to Teacher
    Teacher-->>User: Practice Problem
    
    User->>Supervisor: "Here's my solution: [code]"
    Supervisor->>Examiner: Route to Examiner
    Examiner->>Examiner: Evaluate Solution
    Examiner-->>User: Feedback + Correctness
    
    User->>Supervisor: "How am I doing overall?"
    Supervisor->>Analyst: Route to Analyst
    Analyst->>Analyst: Query User History
    Analyst-->>User: Performance Analysis
```

## 4.3 Component Interaction Diagram

### 4.3.1 Supervisor-Agent Interaction

```mermaid
graph TD
    QUERY[User Query] --> SUP[Supervisor Agent]
    
    SUP --> CACHE{Check Cache}
    CACHE -->|Hit| RETURN[Return Cached]
    CACHE -->|Miss| CLASSIFY[Intent Classification]
    
    CLASSIFY --> COMP[Complexity Analysis]
    COMP --> ROUTE{Route to Agent}
    
    ROUTE -->|teach| TEACH[Teacher Agent]
    ROUTE -->|analyze| ANAL[Analyst Agent]
    ROUTE -->|examine| EXAM[Examiner Agent]
    ROUTE -->|guide| VIS[Visionary Agent]
    ROUTE -->|empath| EMP[Empath Agent]
    
    TEACH --> PROCESS[Process & Generate]
    ANAL --> PROCESS
    EXAM --> PROCESS
    VIS --> PROCESS
    EMP --> PROCESS
    
    PROCESS --> UPDATE_CACHE[Update Cache]
    UPDATE_CACHE --> UPDATE_STATE[Update Dialogue State]
    UPDATE_STATE --> RESPONSE[Return Response]
```

### 4.3.2 RAG Strategy Selection

```mermaid
flowchart TD
    AGENT[Agent Receives Query] --> COMPLEXITY{Check Complexity Score}
    
    COMPLEXITY -->|1-3: Simple| BASE[Baseline RAG]
    COMPLEXITY -->|4-6: Moderate| ADAPT[Adaptive RAG]
    COMPLEXITY -->|7-10: Complex| OMNI[Omni-RAG]
    
    BASE --> VEC1[Vector Search Only]
    VEC1 --> TOPK1[Top-K Documents]
    
    ADAPT --> VEC2[Vector Search]
    ADAPT --> FILTER[Intent-Based Filtering]
    VEC2 --> FILTER
    FILTER --> TOPK2[Top-K Documents]
    
    OMNI --> PARALLEL{Parallel Retrieval}
    PARALLEL --> VEC3[Vector Search]
    PARALLEL --> BM25[BM25 Keyword]
    
    VEC3 --> FUSE[Reciprocal Rank Fusion]
    BM25 --> FUSE
    FUSE --> RERANK[Cross-Encoder Reranking]
    RERANK --> TOPK3[Top-K Documents]
    
    TOPK1 --> PROMPT[Construct LLM Prompt]
    TOPK2 --> PROMPT
    TOPK3 --> PROMPT
```

### 4.3.3 Omni-RAG Internal Architecture

```mermaid
graph TB
    subgraph "Input Processing"
        QUERY[User Query]
        EMBED_Q[Query Embedding]
    end
    
    subgraph "Dual Retrieval"
        VEC_RET[Vector Retriever]
        BM25_RET[BM25 Retriever]
        
        QUERY --> EMBED_Q
        EMBED_Q --> VEC_RET
        QUERY --> BM25_RET
    end
    
    subgraph "Fusion Layer"
        RRF_ALGO[RRF Algorithm]
        SCORE[Score Computation]
        
        VEC_RET -->|Ranked List 1| RRF_ALGO
        BM25_RET -->|Ranked List 2| RRF_ALGO
        RRF_ALGO --> SCORE
    end
    
    subgraph "Reranking Layer"
        CROSS_ENC[Cross-Encoder Model]
        RELEVANCE[Relevance Scoring]
        
        SCORE --> CROSS_ENC
        QUERY --> CROSS_ENC
        CROSS_ENC --> RELEVANCE
    end
    
    subgraph "Output Processing"
        TOPK[Select Top-K]
        COMPRESS[Context Compression]
        FINAL[Final Context]
        
        RELEVANCE --> TOPK
        TOPK --> COMPRESS
        COMPRESS --> FINAL
    end
    
    subgraph "Data Sources"
        CHROMA[(ChromaDB)]
        DOC_STORE[Document Store]
        
        VEC_RET --> CHROMA
        BM25_RET --> DOC_STORE
    end
```

## 4.4 Database Schema

### 4.4.1 Core Tables

```mermaid
erDiagram
    USER ||--o{ SESSION : has
    USER ||--o{ PROGRESS : tracks
    SESSION ||--o{ MESSAGE : contains
    TOPIC ||--o{ LESSON : contains
    LESSON ||--o{ DOCUMENT : has
    USER ||--o{ ENROLLMENT : enrolls
    TOPIC ||--o{ ENROLLMENT : enrolled_in
    
    USER {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        timestamp created_at
        timestamp last_login
        json preferences
    }
    
    SESSION {
        uuid id PK
        uuid user_id FK
        uuid topic_id FK
        timestamp started_at
        timestamp ended_at
        string status
        json state
    }
    
    MESSAGE {
        uuid id PK
        uuid session_id FK
        string role
        text content
        timestamp created_at
        string agent_type
        json metadata
    }
    
    TOPIC {
        uuid id PK
        string name UK
        text description
        string difficulty
        json prerequisites
    }
    
    LESSON {
        uuid id PK
        uuid topic_id FK
        string title
        int order
        text content
        json objectives
    }
    
    DOCUMENT {
        uuid id PK
        uuid lesson_id FK
        string filename
        string file_type
        text content
        vector embedding
        json metadata
        timestamp ingested_at
    }
    
    PROGRESS {
        uuid id PK
        uuid user_id FK
        uuid topic_id FK
        uuid lesson_id FK
        float completion_percent
        json performance_metrics
        timestamp updated_at
    }
    
    ENROLLMENT {
        uuid id PK
        uuid user_id FK
        uuid topic_id FK
        timestamp enrolled_at
        string status
    }
```

### 4.4.2 Vector Storage Structure

**ChromaDB Collections:**
```
brain/
├── {topic_id_1}/
│   └── chroma.sqlite3          # Vector embeddings for topic 1
├── {topic_id_2}/
│   └── chroma.sqlite3          # Vector embeddings for topic 2
└── ...
```

**Collection Metadata:**
- Document ID (UUID)
- Source filename
- Page number (for PDFs)
- Chunk index
- Topic ID
- Timestamp

## 4.5 Security Architecture

### 4.5.1 Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Auth Service
    participant Database
    
    User->>Frontend: Enter Credentials
    Frontend->>Auth Service: Login Request
    Auth Service->>Database: Verify Credentials
    Database-->>Auth Service: User Data
    Auth Service->>Auth Service: Generate JWT
    Auth Service-->>Frontend: Access Token + Refresh Token
    Frontend->>Frontend: Store Tokens
    
    Frontend->>API: Request with Access Token
    API->>API: Validate JWT
    API-->>Frontend: Protected Resource
    
    Note over Frontend,API: Token Expires
    
    Frontend->>Auth Service: Refresh Token Request
    Auth Service->>Auth Service: Validate Refresh Token
    Auth Service-->>Frontend: New Access Token
```

### 4.5.2 Security Layers

**Transport Security:**
- HTTPS/TLS encryption for all communications
- WebSocket Secure (WSS) for real-time connections
- CORS configuration with whitelist

**Application Security:**
- JWT-based stateless authentication
- Password hashing with bcrypt
- SQL injection prevention (parameterized queries)
- XSS protection (input sanitization)
- CSRF protection (Django middleware)

**Data Security:**
- Database encryption at rest
- Sensitive environment variables (API keys)
- Rate limiting per user/IP
- Input validation and sanitization

## 4.6 Scalability Considerations

### 4.6.1 Horizontal Scaling

```mermaid
graph TB
    LB[Load Balancer]
    
    subgraph "API Server Cluster"
        API1[API Server 1]
        API2[API Server 2]
        API3[API Server N]
    end
    
    subgraph "Shared Services"
        REDIS[(Redis Cache)]
        POSTGRES[(PostgreSQL)]
        CHROMA[(ChromaDB)]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> REDIS
    API2 --> REDIS
    API3 --> REDIS
    
    API1 --> POSTGRES
    API2 --> POSTGRES
    API3 --> POSTGRES
    
    API1 --> CHROMA
    API2 --> CHROMA
    API3 --> CHROMA
```

**Scaling Strategies:**
- **API Layer**: Stateless design enables horizontal scaling with load balancer
- **Cache Layer**: Redis cluster for distributed caching
- **Database**: Read replicas for query distribution
- **Vector Store**: Sharding by topic/subject for parallel queries

### 4.6.2 Performance Optimization

**Caching Hierarchy:**
1. **L1**: In-memory cache (per server instance)
2. **L2**: Redis semantic cache (shared)
3. **L3**: Database query cache

**Async Processing:**
- Background tasks for non-critical operations (analytics, logging)
- Celery task queue for heavy computations
- Streaming responses for real-time feedback

**Database Optimization:**
- Indexed columns (user_id, topic_id, session_id)
- Connection pooling
- Query optimization with EXPLAIN ANALYZE
- Materialized views for complex aggregations

## 4.7 Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Frontend"
            NEXT[Next.js Server]
            STATIC[Static Assets CDN]
        end
        
        subgraph "Backend"
            GUNICORN[Gunicorn WSGI Server]
            DJANGO[Django Application]
        end
        
        subgraph "Data Services"
            PG[(PostgreSQL)]
            RD[(Redis)]
            CH[(ChromaDB)]
        end
        
        subgraph "External"
            OPENAI_EXT[OpenAI API]
            GEMINI_EXT[Gemini API]
        end
    end
    
    NEXT --> GUNICORN
    GUNICORN --> DJANGO
    DJANGO --> PG
    DJANGO --> RD
    DJANGO --> CH
    DJANGO --> OPENAI_EXT
    DJANGO --> GEMINI_EXT
    NEXT --> STATIC
```

**Deployment Stack:**
- **Web Server**: Nginx (reverse proxy, static files)
- **Application Server**: Gunicorn with async workers
- **Process Manager**: Systemd or Supervisor
- **Container**: Docker (optional for containerization)
- **Orchestration**: Docker Compose or Kubernetes (production)

---

## 4.8 Critical Gap 1: Voice + Canvas Synchronization Architecture

### 4.8.1 Overview

This architecture addresses the challenge of synchronizing voice-based teaching with handwritten canvas animations, creating a notebook-style learning experience where the AI teacher's voice narration is perfectly synchronized with visual content appearing on the canvas.

### 4.8.2 Architecture Components

```mermaid
graph TB
    subgraph "Content Retrieval & Curation"
        RAG[RAG System] --> CURATOR[Content Curator]
        CURATOR --> CORE[Core Concept Layer]
        CURATOR --> EXAMPLES[Supporting Examples Layer]
        CURATOR --> DEEP[Deep Dive Layer]
    end
    
    subgraph "Teacher Agent Output"
        CORE --> TEACHER[Teacher Agent]
        EXAMPLES --> TEACHER
        DEEP --> TEACHER
        TEACHER --> VOICE_INTENT[Voice Content]
        TEACHER --> VISUAL_INTENT[Visual Intents]
    end
    
    subgraph "Multimodal Output Engine"
        VOICE_INTENT --> TTS[Backend TTS Engine]
        VISUAL_INTENT --> VISUALIZER[Visualizer Agent]
        
        TTS --> AUDIO_STREAM[Audio Stream MP3]
        VISUALIZER --> CANVAS_CMD[Canvas Commands]
        
        CANVAS_CMD --> PEN_TRAIL[Pen Trail Animation]
        CANVAS_CMD --> HANDWRITING[Handwriting Font Rendering]
    end
    
    subgraph "Synchronization Layer"
        SYNC_MGR[Sync Manager]
        AUDIO_STREAM --> SYNC_MGR
        CANVAS_CMD --> SYNC_MGR
        SYNC_MGR --> CHUNK_ACK[Chunk Acknowledgments]
    end
    
    subgraph "Frontend Rendering"
        CHUNK_ACK --> AUDIO_PLAYER[Audio Player]
        CHUNK_ACK --> CANVAS_RENDER[Canvas Renderer]
        
        AUDIO_PLAYER --> SPEAKER[Speaker Output]
        CANVAS_RENDER --> KONVA[React-Konva Canvas]
    end
    
    KONVA --> COMPLETION[Chunk Complete Signal]
    COMPLETION --> SYNC_MGR
```

### 4.8.3 Teacher Output Structure (Hybrid Approach)

The Teacher Agent outputs structured multimodal content:

```json
{
  "teaching_chunks": [
    {
      "id": "chunk_1",
      "voice_content": "Let's understand binary search. It's a divide and conquer algorithm.",
      "visual_intents": [
        {
          "action": "write_heading",
          "content": "Binary Search",
          "style": "handwriting",
          "position": {"x": 100, "y": 50}
        },
        {
          "action": "draw_divider",
          "style": "underline"
        }
      ],
      "pacing": "normal",
      "wait_for_completion": true
    },
    {
      "id": "chunk_2",
      "voice_content": "We start with a sorted array. Here's an example.",
      "visual_intents": [
        {
          "action": "write_array",
          "content": "[1, 3, 5, 7, 9, 11, 13]",
          "style": "handwriting",
          "animate": "pen_trail"
        }
      ],
      "pacing": "normal",
      "wait_for_completion": true
    }
  ],
  "depth_level": "core",
  "student_level": "beginner"
}
