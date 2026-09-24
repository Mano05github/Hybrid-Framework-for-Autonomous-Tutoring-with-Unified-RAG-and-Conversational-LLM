import logging
import json
from .state import AgentState
from llm_engine.factory import LLMFactory
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

# Difficulty level labels mapped from SIP mastery score ranges (v2 spec)
_MASTERY_TO_DIFFICULTY = {
    (0,  40):  "Beginner",
    (40, 70):  "Elementary",
    (70, 85):  "Intermediate",
    (85, 101): "Advanced",
}


def _mastery_to_difficulty(mastery_score: float) -> str:
    """Convert a 0-100 SIP mastery score to a difficulty label."""
    for (lo, hi), label in _MASTERY_TO_DIFFICULTY.items():
        if lo <= mastery_score < hi:
            return label
    return "Intermediate"


class ExaminerAgent:
    """
    The Examiner Agent ("The Quiz Master") — v2 spec compliant.

    Generates 5 MCQs with progressive difficulty.
    Difficulty is read from state['mastery_state'] (SIP) when available,
    otherwise derived from session context.
    """

    def __init__(self):
        self.llm_provider = LLMFactory.get_provider()

    def invoke(self, state: AgentState) -> dict:
        """
        Generates a 5-question mixed-difficulty quiz for the current topic.

        Question difficulty distribution (progressive inside the test):
          Q1: very easy  (recall)
          Q2: easy       (understanding)
          Q3: medium     (application)
          Q4: hard       (analysis)
          Q5: challenge  (synthesis / edge case)

        Scoring weights (used by frontend and AnalystAgent):
          Q1: 10 pts, Q2: 15 pts, Q3: 20 pts, Q4: 25 pts, Q5: 30 pts  → 100 total
        """
        topic = state.get('current_topic', 'General Knowledge')
        mastery_state = state.get('mastery_state') or {}
        topic_mastery = mastery_state.get(topic, 70.0)
        base_difficulty = _mastery_to_difficulty(topic_mastery)

        logger.info(f"[Examiner] Topic={topic!r} | Mastery={topic_mastery} | Base={base_difficulty}")

        system_prompt = (
            "You are Vaathiyar's Examiner — a precise quiz generator for adaptive learning.\n\n"
            f"Topic: '{topic}'\n"
            f"Student mastery level: {base_difficulty} (score {topic_mastery:.0f}/100)\n\n"
            "Generate EXACTLY 5 Multiple Choice Questions with PROGRESSIVE difficulty:\n"
            "  Q1 – very easy (recall / definition)\n"
            "  Q2 – easy (comprehension)\n"
            "  Q3 – medium (application)\n"
            "  Q4 – hard (analysis / tricky edge case)\n"
            "  Q5 – challenge (synthesis or unusual scenario)\n\n"
            "Scoring weights: Q1=10, Q2=15, Q3=20, Q4=25, Q5=30  (total = 100)\n\n"
            "Output MUST be a raw JSON array only — NO markdown, NO extra text.\n"
            "Each element schema:\n"
            "{\n"
            '  "id": <1-5>,\n'
            '  "question": "<question text>",\n'
            '  "code_snippet": "<optional code block or null>",\n'
            '  "options": ["A", "B", "C", "D"],\n'
            '  "correct_index": <0-3>,\n'
            '  "explanation": "<why this is correct>",\n'
            '  "difficulty": "<very_easy|easy|medium|hard|challenge>",\n'
            '  "points": <10|15|20|25|30>\n'
            "}"
        )

        try:
            response_text = self.llm_provider.generate_response(
                prompt=f"Generate a progressive 5-question quiz on: {topic}",
                system_instruction=system_prompt,
            )

            # Strip optional markdown fences
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[-2] if "```" in cleaned[3:] else cleaned[3:]
                cleaned = cleaned.lstrip("json").strip()

            quiz_data = json.loads(cleaned)

            # Enforce exactly 5 questions and correct point values
            point_map = {1: 10, 2: 15, 3: 20, 4: 25, 5: 30}
            for i, q in enumerate(quiz_data[:5], start=1):
                q["id"] = i
                q["points"] = point_map[i]

            quiz_data = quiz_data[:5]

            logger.info(f"[Examiner] Generated {len(quiz_data)} questions for '{topic}'")

            return {
                "messages": [AIMessage(content=f"Quiz ready: {len(quiz_data)} questions on '{topic}'")],
                "quiz_data": quiz_data,
                "next_step": "end",
            }

        except Exception as e:
            logger.error(f"[Examiner] Quiz generation failed: {e}")
            return {
                "messages": [AIMessage(content="I'm having trouble generating the quiz right now. Please try again.")],
                "quiz_data": None,
            }
