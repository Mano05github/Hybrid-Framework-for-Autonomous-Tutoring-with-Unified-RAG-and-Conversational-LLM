from typing import TypedDict, List, Annotated, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    Enhanced Shared Memory for Agent Swarm V2.0
    
    Tracks conversation state, routing decisions, and performance metrics.
    Compatible with voice-first interaction where 'messages' are STT transcripts.
    """
    # Core fields
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str                    # User identifier
    session_id: str                 # Conversation session ID
    query: str                      # Current user query
    
    # Routing fields (V2.0 enhancements)
    intent: str                     # Predicted intent (teacher, coder, examiner, visionary, empath)
    confidence: float               # Classification confidence (0.0-1.0)
    method: str                     # Routing method (cache, setfit, llm)
    latency_ms: float              # Routing latency in milliseconds
    complexity_score: Optional[int] # Query complexity (0-100)
    
    # Context fields
    user_emotion: str              # From Empath Agent (e.g., "Frustrated", "Joyful")
    current_topic: str             # Conversation topic (e.g., "Binary Search Trees")
    next_step: str                 # Router decision (e.g., "teacher", "coder")
    next_agent: Optional[str]      # Next agent to route to (None = end)
    
    # Response fields
    response: str                   # Agent response
    
    # RAG fields (Omni-RAG integration)
    rag_strategy: Optional[str]    # RAG strategy used (no_rag, single_hop, multi_hop, iterative)
    rag_confidence: Optional[float] # RAG retrieval confidence (0.0-1.0)
    sources: Optional[List[str]]   # Retrieved document sources
    teacher_latency_ms: Optional[float]  # Teacher agent total latency
    
    # Mastery tracking
    mastery_state: Optional[dict]  # Student mastery levels from Analyst
    
    # Error handling
    error: Optional[str]           # Error message if any
    
    # === Gap 3: Socratic Coder Agent Fields ===
    code_context: Optional[Dict[str, Any]]  # Code submission context {code, problem_id, time_spent}
    hint_level: Optional[int]      # Hint level delivered (1-5)
    error_type: Optional[str]      # Error type detected (syntax, logic, approach)
    struggle_score: Optional[float] # Struggle score (0.0-1.0)
    
    # === Gap 4: Adaptive Empath Agent Fields ===
    emotion_valence: Optional[float]  # Emotion valence (-1.0 to +1.0)
    emotion_intensity: Optional[str]  # Emotion intensity (mild, moderate, strong)
    intervention_type: Optional[str]  # Intervention type applied
    pause_duration: Optional[float]   # Pause duration in seconds
    
    # === Gap 5: Always-On Visionary Agent Fields ===
    performance_trend: Optional[str]  # Performance trajectory (improving, stable, declining)
    pattern_detected: Optional[Dict[str, Any]]  # Recurring pattern info {type, occurrences, action}
    alert_triggered: Optional[str]    # Alert type if anomaly detected
    forecast_insight: Optional[str]   # Strategic forecast message
    triple_check_mode: Optional[bool] # Whether Triple-Check coordination is active
    visionary_recommendation: Optional[str]  # Strategic recommendation from Visionary
    
    # === Gap 4: Adaptive Empath Agent Fields ===
    emotion_valence: Optional[float] # Emotion valence (-1.0 to +1.0)
    emotion_intensity: Optional[str] # Emotion intensity (mild, moderate, strong)
    intervention_type: Optional[str] # Intervention type (pacing, visualization, branching)
    
    # Voice specifics (optional)
    # user_audio_path: str          # Path to latest user audio (optional, handled by Empath)

