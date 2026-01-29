import logging
from .state import AgentState
from llm_engine.factory import LLMFactory
from rag_system import RAGRetriever 
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

class SupervisorAgent:
    def __init__(self):
        self.llm_provider = LLMFactory.get_provider()
    
    def invoke(self, state: AgentState) -> dict:
        """
        The Router Logic. Decides which agent speaks next.
        """
        messages = state['messages']
        last_user_message = messages[-1].content if messages else ""
        emotion = state.get('user_emotion', 'neutral')
        
        logger.info(f"Supervisor Reasoning: Msg='{last_user_message[:20]}...', Emotion='{emotion}'")

        # 1. Emergency Routing (High Frustration)
        if emotion in ["anger", "frustration", "sadness"]:
            logger.info("Supervisor: Emotion Critical -> Routing to Empath")
            return {"next_step": "empath"}

        # 2. LLM Routing
        # We ask Llama 3.2 to classify the intent.
        system_prompt = (
            "You are the Supervisor of an AI Tutor Team.\n"
            "Analyze the user's request and choose the best agent:\n"
            "1. 'teacher' : For explaining concepts, theory, facts (RAG).\n"
            "2. 'coder'   : For writing code, debugging, practical examples.\n"
            "3. 'examiner': For creating quizzes or tests.\n"
            "4. 'empath'  : For casual chat or emotional support.\n"
            "Return ONLY the agent name (lowercase)."
        )
        
        try:
            # Simple classification call
            decision = self.llm_provider.generate_response(
                prompt=last_user_message,
                system_instruction=system_prompt
            ).strip().lower()
            
            # Clean up response (in case Llama is chatty)
            if "teacher" in decision: decision = "teacher"
            elif "coder" in decision: decision = "coder"
            elif "examiner" in decision: decision = "examiner"
            elif "empath" in decision: decision = "empath"
            else: decision = "teacher" # Default fallback
            
            logger.info(f"Supervisor Decision: {decision}")
            return {"next_step": decision}
            
        except Exception as e:
            logger.error(f"Supervisor Failed: {e}")
            return {"next_step": "teacher"} # Fail safe

class TeacherAgent:
    def __init__(self):
        self.llm_provider = LLMFactory.get_provider()
        self.rag = RAGRetriever()
        
    def invoke(self, state: AgentState) -> dict:
        messages = state['messages']
        query = messages[-1].content
        
        # 1. Retrieve Knowledge
        context = self.rag.get_relevant_context(query)
        
        # 2. Teach
        sys_prompt = "You are a Socratic Teacher. Use the context below to explain."
        if context:
            sys_prompt += f"\nCONTEXT:\n{context}"
            
        response = self.llm_provider.generate_response(query, system_instruction=sys_prompt)
        return {"messages": [AIMessage(content=response)]}

class CoderAgent:
    def __init__(self):
        self.llm_provider = LLMFactory.get_provider()
        
    def invoke(self, state: AgentState) -> dict:
        messages = state['messages']
        query = messages[-1].content
        
        sys_prompt = "You are a Python Tutor. Write clean, commented code. Explain briefly."
        response = self.llm_provider.generate_response(query, system_instruction=sys_prompt)
        return {"messages": [AIMessage(content=response)]}
        
class EmpathAgent:
    def invoke(self, state: AgentState) -> dict:
        # Placeholder: Real logic happens in EmotionService beforehand
        return {"messages": [AIMessage(content="I hear you are frustrated. Let's take a deep breath. How can I help?")]}
