import logging
from .ai_service import AIService  # Kept for safety during transition, but not used
from llm_engine.factory import LLMFactory
from .emotion_service import EmotionService
from .session_phase_controller import SessionPhaseController

logger = logging.getLogger(__name__)


class SessionOrchestrator:
    def __init__(self, session_id=None, user_id=None):
        self.session_id = session_id
        self.user_id    = str(user_id) if user_id else "anonymous"
        self.context = {
            "topic":           "Binary Search Trees",
            "proficiency":     "beginner",
            "code_history":    [],
            "chat_history":    [],
            "current_emotion": "neutral",
            "user_id":         self.user_id,
            "session_id":      session_id or "default",
        }
        try:
            self.llm_provider   = LLMFactory.get_provider()
            self.emotion_service = EmotionService()
            logger.info("LLM Engine & Emotion Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Services: {e}")
            self.llm_provider    = None
            self.emotion_service = None

        # Load SIP mastery snapshot into context
        self._load_sip_context()

        # 5-phase session model (stateful per session)
        self.phase_controller = SessionPhaseController()

    def _load_sip_context(self):
        """Load SIP mastery snapshot into self.context so agents can inject it."""
        if self.user_id == "anonymous":
            return
        try:
            from django.contrib.auth import get_user_model
            from core.models import StudentIntelligenceProfile
            User = get_user_model()
            user = User.objects.get(pk=int(self.user_id))
            sip, _ = StudentIntelligenceProfile.objects.get_or_create(user=user)
            # Update daily streak on session open
            sip.update_streaks()
            sip.save()
            self.context['mastery_state'] = {
                str(tid): sip.get_mastery_score(tid)
                for tid in sip.mastery_map
            }
            self.context['confidence_index']  = sip.confidence_index
            self.context['daily_streak']      = sip.daily_streak
            self.context['learning_style']    = sip.dominant_learning_style()
            self.context['revision_queue']    = sip.revision_priority_queue
            logger.info(f"[SIP] Loaded for user={self.user_id} | style={self.context['learning_style']}")
        except Exception as e:
            logger.warning(f"[SIP] Could not load profile for user={self.user_id}: {e}")

    def update_context(self, event_type, message):
        if event_type == 'chat_message':
            self.context['chat_history'].append({"role": "user", "content": message})
        elif event_type == 'code_change':
            self.context['code_history'].append(message)

    def analyze_emotion(self, audio_path):
        if self.emotion_service:
            self.emotion_service.load_model()
            emotion = self.emotion_service.analyze_audio(audio_path)
            self.context['current_emotion'] = emotion
            print(f"\n🎤 [AUDIO INPUT] Detected Emotion: {emotion.upper()} 🎤\n")
            logger.info(f"Detected Emotion: {emotion}")
            return emotion
        return "neutral"

    def finalize_quiz(self, quiz_answers: list) -> dict:
        """
        Called after the student submits quiz answers.
        quiz_answers: list of dicts like:
          {"id": 1, "correct": True, "points": 10, "time_spent": 12.3}

        Runs AnalystAgent to update SIP mastery and returns updated mastery snapshot.
        """
        from ai_engine.analyst import analyst_agent
        from langchain_core.messages import HumanMessage

        state = {
            "messages":      [HumanMessage(content="quiz_finalized")],
            "user_id":       self.user_id,
            "session_id":    self.context.get("session_id", "default"),
            "query":         "quiz_finalized",
            "intent":        "examiner",
            "confidence":    1.0,
            "method":        "direct",
            "latency_ms":    0.0,
            "current_topic": self.context.get("topic", ""),
            "quiz_data":     quiz_answers,
            "mastery_state": self.context.get("mastery_state", {}),
            "response":      "",
            "next_step":     "",
            "user_emotion":  self.context.get("current_emotion", "neutral"),
        }

        updated_state = analyst_agent(state)

        # Update context with new mastery snapshot
        new_mastery = updated_state.get("mastery_state", {})
        self.context['mastery_state'] = new_mastery

        logger.info(f"[Orchestrator] Quiz finalized — mastery updated for {self.context.get('topic')}")
        return {
            "mastery_state":             new_mastery,
            "consecutive_wrong_answers": updated_state.get("consecutive_wrong_answers", 0),
        }

    def get_ai_response(self, user_message):
        self.update_context('chat_message', user_message)

        try:
            from ai_engine.graph import get_graph
            from langchain_core.messages import HumanMessage

            app = get_graph()
            emotion_label = self.context.get('current_emotion', 'neutral')

            inputs = {
                "messages":      [HumanMessage(content=user_message)],
                "query":         user_message,
                "user_id":       self.context.get('user_id', 'anonymous'),
                "session_id":    self.context.get('session_id', 'default'),
                "user_emotion":  emotion_label,
                "current_topic": self.context.get('topic', 'General'),
                "canvas_mode":   self.context.get('canvas_mode', False),
                # Socratic Mode fields
                "mode":             self.context.get('mode'),
                "topic":            self.context.get('topic') or self.context.get('current_topic_id'),
                "canvas_snapshot":  self.context.get('canvas_snapshot'),
                # SIP snapshot (agents can read mastery level for prompt tuning)
                "mastery_state":    self.context.get('mastery_state', {}),
                # Standard empty fields
                "next_step":     "",
                "intent":        "",
                "confidence":    0.0,
                "method":        "",
                "latency_ms":    0.0,
                "complexity_score": None,
                "next_agent":    None,
                "response":      "",
                # Phase fields (defaults — overwritten below)
                "session_phase":  "",
                "teaching_hint":  None,
                "intent_override": None,
            }

            # ── SessionPhaseController: inject phase context ─────────────────
            _mastery = self.context.get('mastery_state', {})
            _primary_topic = self.context.get('topic') or self.context.get('current_topic_id')
            _mastery_score = float(_mastery.get(str(_primary_topic), 70.0)) if _primary_topic else 70.0
            phase_ctx = self.phase_controller.build_phase_context(user_message, _mastery_score)
            inputs.update(phase_ctx)

            # Clear one-shot fields after injection
            for one_shot in ("current_image", "canvas_snapshot"):
                self.context.pop(one_shot, None)

            logger.info(f"Invoking Swarm for: {user_message[:50]}...")
            final_state = app.invoke(inputs)

            response_text = (
                final_state.get('response')
                or final_state['messages'][-1].content
            )

            if response_text and response_text.strip() == user_message.strip():
                response_text = "I'm still processing your question. Could you give me a moment?"
                logger.warning("Echo detected — blocked response identical to user input")

            intent = final_state.get('intent', None)
            self.context['last_intent'] = intent

            if intent in ['teacher', 'visionary']:
                self.context['canvas_mode'] = True

            self.context['last_teacher_query']    = user_message
            self.context['last_teacher_response'] = response_text
            self.context['last_primary_concept']  = final_state.get('primary_concept')
            self.context['last_canvas_commands']  = final_state.get('canvas_commands', [])
            self.context['last_teaching_script']  = final_state.get('teaching_script', [])
            self.context['last_render_mode']       = final_state.get('render_mode', 'default')
            self.context['last_tree_data']         = final_state.get('tree_data')
            self.context['last_quiz_data']         = final_state.get('quiz_data')
            self.context['last_session_phase']     = self.phase_controller.current_phase()

        except Exception as e:
            logger.error(f"Swarm Error: {e}")
            response_text = "My specialized agents are currently offline. Please try again."

        self.context['chat_history'].append({"role": "assistant", "content": response_text})
        return response_text

    def record_answer(self, correct: bool):
        """Convenience wrapper — delegates to SessionPhaseController.record_answer()."""
        self.phase_controller.record_answer(correct)
        logger.info(f"[Orchestrator] record_answer(correct={correct}) | phase={self.phase_controller.current_phase()}")
