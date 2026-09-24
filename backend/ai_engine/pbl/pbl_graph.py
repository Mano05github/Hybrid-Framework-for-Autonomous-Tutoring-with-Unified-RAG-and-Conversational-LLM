"""
pbl_graph.py — LangGraph for Problem-Based Learning

Graph nodes:
  router        → classifies incoming message type
  hint_node     → Socratic hint generation (uses HintEngine)
  evaluator     → code submission evaluation
  guide_node    → general guidance + canvas snapshot analysis
  empath_node   → frustration detection + empathetic response
    tts_node      → converts text response to audio via Deepgram

Flow:
  router → [hint_node | evaluator | guide_node | empath_node] → tts_node → END

All heavy LLM work is async-compatible (run_in_executor or async LLM calls).
"""

import logging
import os
import subprocess
import sys
from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

RAG_ENABLED = os.getenv('RAG_ENABLED', '1') == '1'
RAG_MAX_CHARS = int(os.getenv('RAG_MAX_CHARS', '1200'))
RAG_MAX_K = int(os.getenv('RAG_MAX_K', '5'))


# ── Code execution helper ─────────────────────────────────────────────────────

def _run_code_safely(code: str, timeout: int = 10):
    """Run student Python code in a subprocess. Returns (stdout, stderr)."""
    try:
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return '', 'TimeoutError: Code took too long to execute.'
    except Exception as exc:
        return '', str(exc)


# ── PBL State ────────────────────────────────────────────────────────────────

class PBLState(TypedDict):
    # Input
    messages: Annotated[List[BaseMessage], operator.add]
    session_id: str
    turn_id: Optional[str]
    user_id: str
    topic_id: Optional[int]
    message_type: str          # 'hint' | 'submit' | 'message' | 'canvas' | 'run_code'

    # Problem context
    concept_name: str
    problem_title: str
    problem_statement: str
    difficulty: int
    hint_number: int
    current_code: Optional[str]
    canvas_snapshot: Optional[str]   # Base64 PNG
    canvas_state: Optional[Dict[str, Any]]  # structured state {text_blocks, drawings, notes}
    time_since_last_action: Optional[float]

    # Session context
    attempt_count: int
    mastery_score: float
    user_emotion: Optional[str]

    # Socratic intelligence (injected by consumers.py before graph invoke)
    teaching_hint: Optional[str]   # directive from SocraticModeEngine
    struggle_type: Optional[str]   # reasoning|syntax_confusion|misconception|guessing|stuck|solved
    progress_state: Optional[str]  # not_started|started|in_progress|almost_done|stuck
    rag_context: Optional[str]
    rag_used: Optional[bool]

    # Output
    response_text: Optional[str]
    response_audio: Optional[bytes]  # raw MP3 bytes
    highlight: Optional[Dict[str, Any]]   # {region, color, duration_ms, reason}
    code_result: Optional[Dict[str, Any]] # {output, success, ai_feedback}
    mastery_update: Optional[Dict[str, Any]]
    route: Optional[str]
    error: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────

def router_node(state: PBLState) -> PBLState:
    """Classify message type and decide which specialist to call."""
    msg_type = state.get('message_type', 'message')
    progress_state = _normalize_progress_state(state)

    # Detect frustration signals in the latest student message
    last_messages = state.get('messages', [])
    latest_text = ''
    if last_messages:
        last = last_messages[-1]
        latest_text = getattr(last, 'content', '') or ''

    frustration_words = ['dont understand', "don't understand", 'confused', 'stuck',
                         'help me', "i give up", 'why', 'what does', 'hard', 'difficult']
    is_frustrated = any(w in latest_text.lower() for w in frustration_words)

    if (
        msg_type not in ('submit', 'run_code')
        and (
            is_frustrated
            or state.get('struggle_type') in ('stuck', 'guessing')
            or progress_state == 'stuck'
        )
    ):
        route = 'empath'
    elif msg_type == 'hint':
        route = 'hint'
    elif msg_type == 'submit':
        route = 'evaluator'
    elif msg_type == 'run_code':
        route = 'run_code'
    elif msg_type == 'canvas':
        route = 'guide'
    else:
        route = 'guide'

    logger.info('[PBLGraph] router → %s (type=%s, progress=%s)', route, msg_type, progress_state)
    return {**state, 'route': route, 'progress_state': progress_state}


def hint_node(state: PBLState) -> PBLState:
    """Generate a Socratic hint via LLM."""
    try:
        from llm_engine.factory import LLMFactory
        llm        = LLMFactory.get_provider()
        hint_level = min(state.get('hint_number', 1), 5)
        problem    = state.get('problem_statement', '')
        code       = state.get('current_code', '') or ''
        teaching_hint = state.get('teaching_hint', '')
        struggle_type = state.get('struggle_type', '')
        progress_state = state.get('progress_state') or _normalize_progress_state(state)
        system     = "You are a Socratic coding tutor. Never give the answer. Guide with questions only."
        if teaching_hint:
            system = f"[TEACHING DIRECTIVE — follow strictly]:\n{teaching_hint}\n\n" + system
        if struggle_type:
            system += f" The student's cognitive state is: {struggle_type}."
        if progress_state:
            system += f" The student's progress stage is: {progress_state}."
        prompt     = (
            f"Problem: {problem}\n\n"
            f"Student's code so far:\n{code}\n\n"
            f"Student progress stage: {progress_state}\n"
            f"Give hint level {hint_level}/5 "
            f"({'very vague' if hint_level == 1 else 'more direct' if hint_level >= 4 else 'moderate'}). "
            "One short paragraph only."
        )
        hint = llm.generate_response(prompt=prompt, system_instruction=system)
        return {**state, 'response_text': hint or "Try breaking the problem into smaller steps."}
    except Exception as exc:
        logger.error('[PBLGraph] hint_node error: %s', exc)
        return {**state, 'response_text': "Try breaking the problem into smaller steps."}


def evaluator_node(state: PBLState) -> PBLState:
    """
    Evaluate submitted code:
    1. Run code safely via subprocess
    2. LLM evaluates correctness against expected output
    3. Returns {output, success, ai_feedback}
    """
    try:
        from llm_engine.factory import LLMFactory
        code    = state.get('current_code', '') or ''
        problem = state.get('problem_statement', '')
        llm     = LLMFactory.get_provider()

        stdout, stderr = _run_code_safely(code)
        run_output = stdout or stderr or 'No output.'

        eval_prompt = (
            f"You are evaluating a student's Python code for a PBL problem.\n\n"
            f"Problem:\n{problem}\n\n"
            f"Student Code:\n{code}\n\n"
            f"Code Output:\n{run_output}\n\n"
            f"First line must be exactly 'CORRECT' or 'INCORRECT'.\n"
            f"Then give 2-3 sentences of Socratic feedback (don't reveal the full answer if incorrect)."
        )
        raw = llm.generate_response(
            prompt=eval_prompt,
            system_instruction="You are a concise, encouraging coding tutor.",
        )
        is_correct = (raw or '').strip().upper().startswith('CORRECT')
        parts      = (raw or '').strip().split('\n', 1)
        feedback   = parts[1].strip() if len(parts) > 1 else raw or ''

        return {
            **state,
            'code_result': {'output': run_output, 'success': is_correct, 'ai_feedback': feedback},
            'response_text': feedback,
        }
    except Exception as exc:
        logger.error('[PBLGraph] evaluator_node error: %s', exc)
        return {
            **state,
            'code_result': {'output': 'Error running code.', 'success': False, 'ai_feedback': ''},
            'response_text': "I had trouble checking your code. Try again!",
        }


def run_code_node(state: PBLState) -> PBLState:
    """Execute code without evaluation, return raw output."""
    try:
        code = state.get('current_code', '') or ''
        stdout, stderr = _run_code_safely(code)
        return {
            **state,
            'code_result': {
                'output':  stdout or stderr or 'No output.',
                'success': not bool(stderr),
                'ai_feedback': '',
            },
        }
    except Exception as exc:
        logger.error('[PBLGraph] run_code_node error: %s', exc)
        return {
            **state,
            'code_result': {'output': str(exc), 'success': False, 'ai_feedback': ''},
        }


def guide_node(state: PBLState) -> PBLState:
    """
    General guidance + optional canvas analysis.
    If canvas_snapshot present → analyze visually and add highlight.
    """
    try:
        from llm_engine.factory import LLMFactory
        llm = LLMFactory.get_provider()

        canvas_b64    = state.get('canvas_snapshot')
        code          = state.get('current_code', '')
        problem       = state.get('problem_statement', '')
        concept       = state.get('concept_name', '')
        mastery       = state.get('mastery_score', 0)
        messages      = state.get('messages', [])
        teaching_hint = state.get('teaching_hint', '')
        struggle_type = state.get('struggle_type', '')
        progress_state = state.get('progress_state') or _normalize_progress_state(state)
        canvas_state   = state.get('canvas_state')
        canvas_summary = _summarize_canvas_state(canvas_state)
        topic_id       = state.get('topic_id')
        student_msg   = ''
        if messages:
            last = messages[-1]
            student_msg = getattr(last, 'content', '') or ''

        rag_context = ''
        if _should_use_rag(student_msg, struggle_type, progress_state, topic_id):
            rag_context = _retrieve_rag_context(student_msg, topic_id)

        base_system = (
            "You are an AI tutor for a Problem-Based Learning session. "
            "Never give away the answer directly — always guide through questions. "
            "Keep responses concise (2-4 sentences). "
            "If you can identify a region on the canvas to highlight, add a JSON block at the end:\n"
            '```highlight\n{"x":0.0,"y":0.0,"w":0.2,"h":0.1,"reason":"explanation","color":"rgba(252,200,100,0.35)"}\n```'
        )
        # Inject Socratic directive and cognitive context at the front
        directive = ''
        if teaching_hint:
            directive += f"[TEACHING DIRECTIVE — follow strictly]:\n{teaching_hint}\n\n"
        if struggle_type:
            directive += f"[Student cognitive state: {struggle_type}] — tailor your response accordingly.\n\n"
        if progress_state:
            directive += (
                f"[Student progress stage: {progress_state}] — prioritize Observe -> Diagnose -> Guide. "
                "Do not jump to full solutions.\n\n"
            )
        system_prompt = directive + base_system

        user_content = (
            f"Problem: {problem}\n"
            f"Concept: {concept}\n"
            f"Student's current code:\n{code}\n\n"
            f"Student canvas summary: {canvas_summary}\n"
            f"Student progress stage: {progress_state}\n"
            f"Student says: {student_msg}\n"
            f"Mastery: {mastery:.0%}"
        )
        if rag_context:
            user_content += f"\n\nGrounding context (use only if relevant):\n{rag_context}"

        # Include canvas image if available
        if canvas_b64:
            response = llm.generate_vision_response(
                prompt=user_content,
                image_base64=canvas_b64,
                system_instruction=system_prompt,
            )
        else:
            response = llm.generate_response(
                prompt=user_content,
                system_instruction=system_prompt,
            )

        # Parse highlight from response
        highlight = _extract_highlight(response or '')
        clean_response = _strip_highlight_block(response or '')

        return {
            **state,
            'response_text': clean_response,
            'highlight': highlight,
            'rag_context': rag_context,
            'rag_used': bool(rag_context),
        }
    except Exception as exc:
        logger.error('[PBLGraph] guide_node error: %s', exc)
        return {**state, 'response_text': "Keep going! Try working through the problem step by step."}


def empath_node(state: PBLState) -> PBLState:
    """Respond empathetically when student shows frustration."""
    try:
        from llm_engine.factory import LLMFactory
        llm           = LLMFactory.get_provider()
        messages      = state.get('messages', [])
        last_msg      = getattr(messages[-1], 'content', '') if messages else ''
        teaching_hint = state.get('teaching_hint', '')
        base_system   = (
            "You are an empathetic AI tutor. The student seems frustrated or confused. "
            "Acknowledge their feelings briefly, then gently redirect with one Socratic question. "
            "Keep it to 2-3 sentences. Never lecture. Never give the answer directly."
        )
        system = (f"[TEACHING DIRECTIVE — follow strictly]:\n{teaching_hint}\n\n" + base_system
                  if teaching_hint else base_system)
        prompt = (
            f"Problem: {state.get('problem_statement', '')}\n"
            f"Student said: {last_msg}\n"
            f"Mastery: {state.get('mastery_score', 0):.0%}"
        )
        response = llm.generate_response(prompt=prompt, system_instruction=system)
        return {**state, 'response_text': response or "You're doing great — keep going!"}
    except Exception as exc:
        logger.error('[PBLGraph] empath_node error: %s', exc)
        return {**state, 'response_text': "I can see you're working hard — let's tackle it step by step!"}


def tts_node(state: PBLState) -> PBLState:
    """Convert response_text to audio via Deepgram TTS (teacher_qa model mapping)."""
    text = state.get('response_text', '')
    if not text:
        return state

    try:
        from ai_engine.tts import get_tts_engine
        audio = get_tts_engine().generate_speech(text, agent='teacher_qa')
        return {**state, 'response_audio': audio}
    except Exception as exc:
        logger.warning('[PBLGraph] TTS node error (non-fatal): %s', exc)
        return {**state, 'response_audio': b''}


# ── Routing helpers ───────────────────────────────────────────────────────────

def _route_after_router(state: PBLState) -> str:
    return state.get('route', 'guide')


# ── Graph compilation ────────────────────────────────────────────────────────

def build_pbl_graph():
    workflow = StateGraph(PBLState)

    workflow.add_node('router',   router_node)
    workflow.add_node('hint',     hint_node)
    workflow.add_node('evaluator', evaluator_node)
    workflow.add_node('run_code', run_code_node)
    workflow.add_node('guide',    guide_node)
    workflow.add_node('empath',   empath_node)
    workflow.add_node('tts',      tts_node)

    workflow.set_entry_point('router')

    workflow.add_conditional_edges(
        'router',
        _route_after_router,
        {
            'hint':     'hint',
            'evaluator':'evaluator',
            'run_code': 'run_code',
            'guide':    'guide',
            'empath':   'empath',
        }
    )

    # All content nodes → TTS
    for node in ('hint', 'evaluator', 'guide', 'empath'):
        workflow.add_edge(node, 'tts')

    # run_code skips TTS (just returns output)
    workflow.add_edge('run_code', END)
    workflow.add_edge('tts', END)

    app = workflow.compile()
    logger.info('[PBLGraph] Compiled ✅')
    return app


# Singleton
_pbl_graph = None

def get_pbl_graph():
    global _pbl_graph
    if _pbl_graph is None:
        _pbl_graph = build_pbl_graph()
    return _pbl_graph


# ── Parse helpers ─────────────────────────────────────────────────────────────

import re, json as _json

def _extract_highlight(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r'```highlight\s*(\{.*?\})\s*```', text, re.DOTALL)
    if not m:
        return None
    try:
        data = _json.loads(m.group(1))
        region = {k: data[k] for k in ('x', 'y', 'w', 'h') if k in data}
        return {
            'region':      region,
            'color':       data.get('color', 'rgba(252,200,100,0.35)'),
            'reason':      data.get('reason', ''),
            'duration_ms': data.get('duration_ms', 4000),
        }
    except Exception:
        return None


def _strip_highlight_block(text: str) -> str:
    return re.sub(r'```highlight\s*\{.*?\}\s*```', '', text, flags=re.DOTALL).strip()


def _summarize_canvas_state(canvas_state: Optional[Dict[str, Any]]) -> str:
    if not canvas_state:
        return 'No canvas artifacts available.'

    text_blocks = canvas_state.get('text_blocks') or []
    drawings = canvas_state.get('drawings') or []
    notes = canvas_state.get('notes') or []

    parts = []
    if text_blocks:
        parts.append(f"text_blocks={len(text_blocks)}")
    if drawings:
        parts.append(f"drawings={len(drawings)}")
    if notes:
        parts.append(f"notes={len(notes)}")

    if not parts:
        return 'Canvas present but currently blank.'

    return ', '.join(parts)


def _normalize_progress_state(state: PBLState) -> str:
    if state.get('progress_state') in ('not_started', 'started', 'in_progress', 'almost_done', 'stuck'):
        return state['progress_state']

    struggle = state.get('struggle_type')
    if struggle == 'stuck':
        return 'stuck'

    code = (state.get('current_code') or '').strip()
    canvas_state = state.get('canvas_state') or {}
    time_idle = float(state.get('time_since_last_action') or 0.0)
    attempts = int(state.get('attempt_count') or 0)

    has_canvas = bool(
        (canvas_state.get('text_blocks') or [])
        or (canvas_state.get('drawings') or [])
        or (canvas_state.get('notes') or [])
    )

    if not code and not has_canvas and attempts == 0:
        return 'not_started'

    if time_idle >= 30:
        return 'stuck'

    if code and ('return ' in code or 'print(' in code or 'def ' in code) and attempts >= 1:
        return 'almost_done'

    if code and (('for ' in code) or ('while ' in code) or ('if ' in code)):
        return 'in_progress'

    if code or has_canvas:
        return 'started'

    return 'stuck'


def _should_use_rag(
    student_msg: str,
    struggle_type: Optional[str],
    progress_state: Optional[str],
    topic_id: Optional[int],
) -> bool:
    if not RAG_ENABLED:
        return False
    if not topic_id:
        return False

    text = (student_msg or '').strip().lower()
    if not text:
        return False

    concept_markers = (
        'what is',
        'why',
        'explain',
        'difference between',
        'how does',
    )
    explicit_concept = any(marker in text for marker in concept_markers)
    misconception_signal = struggle_type in ('misconception', 'reasoning')
    stuck_signal = progress_state == 'stuck'

    return explicit_concept or misconception_signal or stuck_signal


def _retrieve_rag_context(student_msg: str, topic_id: int) -> str:
    try:
        from rag.retriever import retrieve_context
        return retrieve_context(
            query=student_msg,
            topic_id=topic_id,
            k=RAG_MAX_K,
            max_chars=RAG_MAX_CHARS,
        )
    except Exception as exc:
        logger.warning('[PBLGraph] RAG retrieval skipped: %s', exc)
        return ''
