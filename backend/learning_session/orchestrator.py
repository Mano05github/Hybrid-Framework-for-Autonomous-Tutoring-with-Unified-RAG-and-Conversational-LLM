import logging
from .ai_service import AIService # Kept for safety during transition, but not used
from llm_engine.factory import LLMFactory
from .emotion_service import EmotionService
from rag_system import RAGRetriever

logger = logging.getLogger(__name__)

class SessionOrchestrator:
    def __init__(self, session_id=None):
        self.session_id = session_id
        self.context = {
            "topic": "Binary Search Trees",
            "proficiency": "beginner",
            "code_history": [],
            "chat_history": [],
            "current_emotion": "neutral" 
        }
        try:
            # self.ai_service = AIService() # DEPRECATED
            self.llm_provider = LLMFactory.get_provider() # NEW ENGINE
            self.emotion_service = EmotionService()
            self.rag_retriever = RAGRetriever() # NEW LIBRARY
            logger.info("LLM Engine, Emotion & RAG Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Services: {e}")
            self.llm_provider = None
            self.emotion_service = None
            self.rag_retriever = None

    def update_context(self, event_type, message):
        """
        Updates the session context based on frontend events.
        """
        if event_type == 'chat_message':
            self.context['chat_history'].append({"role": "user", "content": message})
        elif event_type == 'code_change':
            self.context['code_history'].append(message) # message is dict with code/language

    def analyze_emotion(self, audio_path):
        """
        Analyzes audio for emotion and updates context.
        """
        if self.emotion_service:
             # Ensure model is ready (lazy load trigger)
             self.emotion_service.load_model()
             emotion = self.emotion_service.analyze_audio(audio_path)
             self.context['current_emotion'] = emotion
             # Visual Verification Log
             print(f"\n🎤 [AUDIO INPUT] Detected Emotion: {emotion.upper()} 🎤\n")
             logger.info(f"Detected Emotion: {emotion}")
             return emotion
        return "neutral"

    def get_ai_response(self, user_message):
        """
        Determines the AI's response logic.
        """
        self.update_context('chat_message', user_message)
        
        # Swarm Logic: Delegate to the Agent Graph
        try:
            from ai_engine.graph import app
            from langchain_core.messages import HumanMessage
            
            emotion_label = self.context.get('current_emotion', 'neutral')
            
            # 1. Build State
            inputs = {
                "messages": [HumanMessage(content=user_message)],
                "user_emotion": emotion_label,
                "current_topic": self.context.get('topic', 'General'),
                "current_image": self.context.get('current_image', None), # Inject Image
                "next_step": ""
            }
            
            # Clear image after one use to avoid stale seeing
            if "current_image" in self.context:
                del self.context["current_image"]
            
            # 2. Invoke Swarm
            logger.info(f"Invoking Swarm for: {user_message[:50]}...")
            final_state = app.invoke(inputs)
            
            # 3. Extract Response
            response_text = final_state['messages'][-1].content
            logger.info("Swarm Response Received")

        except Exception as e:
            logger.error(f"Swarm Error: {e}")
            response_text = "My specialized agents are currently offline. Please try again."

        self.context['chat_history'].append({"role": "assistant", "content": response_text})
        return response_text
