import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


# ── Mapping from struggle_type → student_strategy ────────────────────────────
_STRATEGY_MAP = {
    "syntax_confusion": "trial_and_error",
    "misconception":    "trial_and_error",
    "guessing":         "guessing",
    "stuck":            "stuck",
    "reasoning":        "systematic_reasoning",
    "solved":           "systematic_reasoning",
}


class ChatView(APIView):
    """
    Unified Socratic AI Tutor endpoint.

    Accepts JSON body:
    {
        "query":                        str,          # student message / speech transcript
        "session_id":                   str,          # conversation session id
        "pbl_session_id":               str | null,   # active PBLSession UUID
        "canvas_state":                 dict | null,  # {text_blocks, drawings, notes}
        "speech_transcript":            str | null,   # raw STT transcript (may duplicate query)
        "time_since_last_action_seconds": float,      # inactivity timer from frontend
        "code":                         str | null,   # current code in editor
        "topic_id":                     int | null,   # core.Topic pk for RAG
    }

    Returns:
    {
        "response":     str,
        "mode":         str,   # listener | nudge | deep_guidance | reflection
        "render_mode":  str,   # default | canvas | tree | voice
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        query        = (data.get("query") or "").strip()
        session_id   = str(data.get("session_id") or f"user_{request.user.id}_session")
        pbl_session_id        = data.get("pbl_session_id")
        canvas_state          = data.get("canvas_state")          # structured JSON
        speech_transcript     = data.get("speech_transcript", "")
        time_since_last_action = float(data.get("time_since_last_action_seconds") or 0.0)
        code                  = data.get("code", "")
        topic_id              = data.get("topic_id")

        if not query:
            return Response({"error": "query is required."}, status=status.HTTP_400_BAD_REQUEST)

        # ── 1. Initialise base AgentState ─────────────────────────────────────
        from langchain_core.messages import HumanMessage
        state = {
            "messages":       [HumanMessage(content=query)],
            "user_id":        str(request.user.id),
            "session_id":     session_id,
            "query":          query,
            # Routing defaults
            "intent":         "teacher",
            "confidence":     1.0,
            "method":         "direct",
            "latency_ms":     0.0,
            "complexity_score": 50,
            # Context
            "user_emotion":   "",
            "current_topic":  "",
            "current_topic_id": str(topic_id) if topic_id else None,
            "next_step":      "",
            "next_agent":     None,
            "context":        None,
            # Response defaults
            "response":       "",
            "teaching_script": None,
            "canvas_mode":    False,
            "canvas_commands": [],
            "primary_concept": None,
            # Render mode
            "render_mode":    "default",
            "tree_data":      None,
            # Socratic
            "mode":           "socratic_tutor",
            "topic":          None,
            "canvas_snapshot": None,
            # New Socratic intelligence fields
            "canvas_state":           canvas_state,
            "time_since_last_action": time_since_last_action,
            "struggle_type":          None,
            "student_strategy":       None,
            # PBL
            "pbl_session_id":         pbl_session_id,
            "pbl_concept_name":       None,
            "pbl_problem_title":      None,
            "pbl_problem_statement":  None,
            "pbl_difficulty":         None,
            "pbl_attempt_count":      0,
            "pbl_hint_count":         0,
            "pbl_mastery_score":      0.0,
            "pbl_current_code":       code or None,
        }

        # ── 2. Enrich with PBL session data ───────────────────────────────────
        is_solved = False
        attempt_count = 0
        hint_count    = 0

        if pbl_session_id:
            try:
                from ai_engine.pbl.models import PBLSession
                pbl_session = PBLSession.objects.select_related(
                    "concept__topic__subject"
                ).get(pk=pbl_session_id, user=request.user)

                attempt_count = pbl_session.attempt_count
                hint_count    = pbl_session.hint_count
                is_solved     = pbl_session.status == "completed"

                state["pbl_concept_name"]      = pbl_session.concept.topic.title if pbl_session.concept else ""
                state["pbl_problem_title"]     = pbl_session.problem_title
                state["pbl_problem_statement"] = pbl_session.problem_statement
                state["pbl_difficulty"]        = pbl_session.difficulty_level
                state["pbl_attempt_count"]     = attempt_count
                state["pbl_hint_count"]        = hint_count
                state["pbl_mastery_score"]     = pbl_session.mastery_score
                state["current_topic"]         = pbl_session.concept.topic.title if pbl_session.concept else ""
                state["current_topic_id"]      = str(pbl_session.concept.topic_id) if pbl_session.concept else state["current_topic_id"]

                # Inject problem context into the query so the teacher has full awareness
                if pbl_session.problem_statement:
                    state["context"] = (
                        f"Problem: {pbl_session.problem_title}\n"
                        f"{pbl_session.problem_statement}"
                    )

            except Exception as exc:
                logger.warning("[ChatView] PBL session fetch failed (non-fatal): %s", exc)

        # ── 3. Run Cognitive Struggle Detector ────────────────────────────────
        try:
            from ai_engine.cognitive_state_detector import get_cognitive_detector
            detector = get_cognitive_detector()
            struggle_state = detector.detect(
                canvas_state=canvas_state,
                code=code,
                attempt_count=attempt_count,
                speech_transcript=speech_transcript or query,
                time_since_last_action=time_since_last_action,
                is_solved=is_solved,
            )
            state["struggle_type"]    = struggle_state.type
            state["student_strategy"] = _STRATEGY_MAP.get(struggle_state.type, "systematic_reasoning")
            logger.info("[ChatView] Struggle: %s (%.2f) — %s", struggle_state.type, struggle_state.confidence, struggle_state.evidence)
        except Exception as exc:
            logger.warning("[ChatView] Cognitive detector failed (non-fatal): %s", exc)
            struggle_state = None

        # ── 4. Run Socratic Mode Engine ────────────────────────────────────────
        try:
            from ai_engine.socratic_mode_engine import get_socratic_engine
            engine = get_socratic_engine()
            decision = engine.decide_mode(
                is_solved=is_solved,
                attempt_count=attempt_count,
                hint_count=hint_count,
                time_since_last_action=time_since_last_action,
                struggle_state=struggle_state,
            )
            state["teaching_hint"] = decision.teaching_hint
            socratic_mode_label    = decision.mode
            logger.info("[ChatView] Socratic mode: %s", socratic_mode_label)
        except Exception as exc:
            logger.warning("[ChatView] Socratic engine failed (non-fatal): %s", exc)
            socratic_mode_label = "nudge"
            state["teaching_hint"] = ""

        # ── 5. Invoke the agent graph ──────────────────────────────────────────
        try:
            from ai_engine.graph import get_graph
            graph = get_graph()
            result_state = graph.invoke(state)
        except Exception as exc:
            logger.exception("[ChatView] Graph invocation failed: %s", exc)
            return Response(
                {"error": "AI tutor temporarily unavailable. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── 6. Build response — never include canvas_commands in Socratic mode ─
        response_payload = {
            "response":    result_state.get("response", ""),
            "mode":        socratic_mode_label,
            "render_mode": result_state.get("render_mode", "default"),
        }

        return Response(response_payload, status=status.HTTP_200_OK)


class PBLRuntimeStatsView(APIView):
    """Read-only runtime telemetry for canary monitoring."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ai_engine.pbl.runtime_metrics import snapshot

        return Response(snapshot(), status=status.HTTP_200_OK)
