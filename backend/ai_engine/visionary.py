import logging
import base64
from typing import Dict, Any
from langchain_core.messages import AIMessage
from .state import AgentState
from llm_engine.factory import LLMFactory

logger = logging.getLogger(__name__)

class VisionaryAgent:
    """
    The Visionary Agent ("The Eyes").
    Analyzes visual input (whiteboard drawings, etc.) using Multimodal LLMs.
    """
    def __init__(self):
        self.llm_provider = LLMFactory.get_provider()
        
    def invoke(self, state: AgentState) -> dict:
        """
        Analyzes the image present in the state.
        """
        messages = state['messages']
        image_data = state.get('current_image') # Expecting Base64 string
        user_prompt = messages[-1].content if messages else "Analyze this image."
        
        # Guard Clause: No Image?
        if not image_data:
            logger.warning("Visionary Agent called but no 'current_image' found in state.")
            return {
                "messages": [AIMessage(content="I don't see anything on the board yet. Draw something first!")],
                "next_step": "end"
            }

        logger.info(f"Visionary: Analyzing Image (Prompt: {user_prompt})")
        
        try:
            # 1. Clean Base64 header if present (data:image/png;base64,...)
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]
            
            # 2. Call Vision Model
            response_text = self.llm_provider.generate_vision_response(
                prompt=user_prompt,
                image_base64=image_data,
                system_instruction="You are a Visionary Tutor. Analyze the student's diagram/handwriting on the whiteboard. Explain what you see and check for correctness."
            )
            
            logger.info("Visionary: Analysis Complete")
            
            return {
                "messages": [AIMessage(content=response_text)],
                "next_step": "end"
            }
            
        except Exception as e:
            logger.error(f"Visionary Analysis Failed: {e}")
            return {
                "messages": [AIMessage(content="My eyes are a bit blurry right now. I couldn't process the image.")]
            }
