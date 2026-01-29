import os
import logging
from google import genai
from google.genai import types
from llm_engine.interfaces import LLMProvider

logger = logging.getLogger(__name__)

class GoogleGeminiProvider(LLMProvider):
    def __init__(self):
        # 1. API Key Check
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
            raise ValueError("GOOGLE_API_KEY not set")
        
        # 2. Initialize Client
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash" 
        logger.info(f"Initialized Google Gemini Provider with model: {self.model_name}")

    def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        try:
            # Use default system instruction if none provided
            if not system_instruction:
                system_instruction = "You are a wise Socratic Tutor for Computer Science. Guide the student by asking questions, not just giving answers. Be concise."

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini Generation Failed: {e}")
            return f"I'm sorry, my cloud brain is having trouble. (Error: {str(e)})"

    def generate_vision_response(self, prompt: str, image_base64: str, system_instruction: str = None) -> str:
        try:
            # Construct the Image Part
            # Gemini 2.0 Flash expects 'parts' list with text and inline_data
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                     types.Part.from_text(text=prompt),
                     types.Part.from_bytes(data=image_base64, mime_type="image/png") # Assuming PNG from canvas
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction or "You are a Helpful Vision Assistant. Analyze the diagram."
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini Vision Failed: {e}")
            return f"I cannot see right now. (Error: {str(e)})"
