from typing import TypedDict, List, Annotated, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    Shared Memory for Agent Swarm V3.0

    Covers: routing, teaching, RAG, canvas, Socratic mode, empath, visionary,
    examiner, SIP mastery, session phases, and v3 render-mode switching.
    """
    # ── Core ────────────────────────────────────────────────────────────────
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    session_id: str
    query: str

    # ── Routing ─────────────────────────────────────────────────────────────
    intent: str                          # teacher | coder | examiner | visionary | empath | general
    confidence: float                    # 0.0 – 1.0
    method: str                          # instant_keyword | cache | setfit | llm
    latency_ms: float
    complexity_score: Optional[int]      # 0 – 100

    # ── Context ─────────────────────────────────────────────────────────────
    user_emotion: str
    current_topic: str
    current_topic_id: Optional[str]      # numeric topic pk as string for RAG
    next_step: str
    next_agent: Optional[str]
    context: Optional[str]               # arbitrary context string

    # ── Response ────────────────────────────────────────────────────────────
    response: str
    teaching_script: Optional[List[Dict[str, Any]]]
    canvas_mode: Optional[bool]          # legacy flag; prefer render_mode
    canvas_commands: Optional[List[Dict[str, Any]]]  # beat list for frontend
    primary_concept: Optional[str]       # extracted concept for visualization

    # ── v3 Render Mode ──────────────────────────────────────────────────────
    render_mode: Optional[str]           # "tree" | "canvas" | "default"
    tree_data: Optional[Dict[str, Any]]  # hierarchical tree structure for Tree Mode

    # ── Socratic Mode ───────────────────────────────────────────────────────
    mode: Optional[str]                  # 'socratic_tutor'
    topic: Optional[str]                 # topic slug e.g. 'binary_search'
    canvas_snapshot: Optional[str]       # Base64 PNG of student canvas

    # ── RAG ─────────────────────────────────────────────────────────────────
    rag_strategy: Optional[str]
    rag_confidence: Optional[float]
    sources: Optional[List[str]]
    teacher_latency_ms: Optional[float]
    difficulty_bias: Optional[str]       # "struggling" | "confident" | None

    # ── Performance latency breakdown ────────────────────────────────────────
    phase1_latency_ms: Optional[float]
    phase2_latency_ms: Optional[float]
    phase3_latency_ms: Optional[float]
    performance_metrics: Optional[Dict[str, Any]]

    # ── Mastery / SIP ───────────────────────────────────────────────────────
    mastery_state: Optional[dict]        # topic → score snapshot
    consecutive_wrong_answers: Optional[int]   # for adaptive difficulty engine
    session_phase: Optional[str]         # diagnostic|explanation|practice|adjustment|minitest
    teaching_hint: Optional[str]         # phase-specific instruction injected into teacher prompt
    intent_override: Optional[str]       # forces supervisor to route to specific agent (e.g. minitest → examiner)

    # ── Examiner / Quiz ─────────────────────────────────────────────────────
    quiz_data: Optional[Dict[str, Any]]  # structured quiz from ExaminerAgent

    # ── Error ───────────────────────────────────────────────────────────────
    error: Optional[str]

    # ── Gap 3: Socratic Coder ───────────────────────────────────────────────
    code_context: Optional[Dict[str, Any]]
    hint_level: Optional[int]
    error_type: Optional[str]
    struggle_score: Optional[float]

    # ── PBL (Problem-Based Learning) ─────────────────────────────────────────
    pbl_session_id: Optional[str]        # UUID of the active PBLSession
    pbl_concept_name: Optional[str]      # ConceptNode.topic.title
    pbl_problem_title: Optional[str]
    pbl_problem_statement: Optional[str]
    pbl_difficulty: Optional[int]        # 1–5
    pbl_attempt_count: Optional[int]
    pbl_hint_count: Optional[int]
    pbl_mastery_score: Optional[float]   # 0.0–1.0
    pbl_current_code: Optional[str]      # latest code from canvas code block

    # ── Socratic Intelligence ───────────────────────────────────────────────
    canvas_state: Optional[Dict[str, Any]]  # structured {text_blocks, drawings, notes} — student-owned
    struggle_type: Optional[str]            # reasoning|syntax_confusion|misconception|guessing|stuck|solved
    student_strategy: Optional[str]         # guessing|trial_and_error|systematic_reasoning|stuck
    time_since_last_action: Optional[float] # seconds since last student action (sent by frontend)

    # ── Gap 4: Adaptive Empath ──────────────────────────────────────────────
    emotion_valence: Optional[float]     # -1.0 to +1.0
    emotion_intensity: Optional[str]     # mild | moderate | strong
    intervention_type: Optional[str]     # pacing_adjustment | visualization | branching | encouragement | break_suggestion
    pause_duration: Optional[float]      # seconds
    emotion_context: Optional[str]       # coaching note written by empath for teacher

    # ── Gap 5: Visionary ────────────────────────────────────────────────────
    performance_trend: Optional[str]     # improving | stable | declining
    pattern_detected: Optional[Dict[str, Any]]
    alert_triggered: Optional[str]
    forecast_insight: Optional[str]
    triple_check_mode: Optional[bool]
    visionary_recommendation: Optional[str]
    recent_errors: Optional[int]
    velocity_score: Optional[float]
    mouse_events: Optional[int]
    keypress_count: Optional[int]
    activity_type: Optional[str]         # learning | coding | assessment

