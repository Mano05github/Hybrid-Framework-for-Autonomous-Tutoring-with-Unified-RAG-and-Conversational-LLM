import logging
import json
from .state import AgentState
from llm_engine.factory import LLMFactory
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

class ExaminerAgent:
    """
    The Examiner Agent ("The Quiz Master").
    Generates structured quizzes (JSON) based on the user's current topic.
    """
    def __init__(self):
        self.llm_provider = LLMFactory.get_provider()
        
    def invoke(self, state: AgentState) -> dict:
        """
        Generates a 5-question quiz for the current topic.
        """
        messages = state['messages']
        topic = state.get('current_topic', 'General Programming')
        difficulty = "Intermediate" # Could be dynamic based on Analyst
        
        logger.info(f"Examiner: Generating {difficulty} quiz for {topic}")
        
        # 1. Construct Prompt for JSON Output
        system_prompt = (
            "You are an Examiner for a Computer Science Exam.\n"
            f"Generate a {difficulty} level quiz on the topic: '{topic}'.\n"
            "Create exactly 3 Multiple Choice Questions.\n"
            "Output MUST be raw JSON only. No markdown formatting.\n"
            "Schema:\n"
            "[\n"
            "  {\n"
            "    \"id\": 1,\n"
            "    \"question\": \"Question text...\",\n"
            "    \"code_snippet\": \"Optional code block (or null)\",\n"
            "    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"],\n"
            "    \"correct_index\": 0,\n"
            "    \"explanation\": \"Brief explanation of why.\"\n"
            "  }\n"
            "]"
        )
        
        try:
            # 2. Call LLM
            # We use a mocked user message to trigger generation if the last message wasn't clear
            response_text = self.llm_provider.generate_response(
                prompt=f"Create a quiz for {topic}", 
                system_instruction=system_prompt
            )
            
            # 3. Clean and Parse JSON
            # Llama might wrap in ```json ... ```
            cleaned_json = response_text.replace("```json", "").replace("```", "").strip()
            quiz_data = json.loads(cleaned_json)
            
            # 4. Return as a Special Message Type
            # The Frontend will detect "type": "quiz_command"
            return {
                "messages": [AIMessage(content=str(quiz_data))], # Log raw content
                "quiz_data": quiz_data, # Structured data for UI
                "next_step": "end" # Setup to end turn or wait for answer
            }
            
        except Exception as e:
            logger.error(f"Examiner JSON Gen Failed: {e}")
            # Fallback text
            return {"messages": [AIMessage(content="I'm having trouble printing the quiz papers right now. Let's try again.")]}
