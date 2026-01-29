import os
from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
            raise ValueError("GOOGLE_API_KEY not set")
        
        # Initialize the new Client
        self.client = genai.Client(api_key=api_key)
        # We will use the model we confirmed exists
        self.model_name = "gemini-2.0-flash" 

    def generate_response(self, prompt_text):
        """
        Generates a response from the AI model.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    system_instruction="You are a wise Socratic Tutor for Computer Science. Guide the student by asking questions, not just giving answers. Be concise."
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"AI Generation Failed: {e}")
            return f"I'm sorry, I'm having trouble thinking right now. (Error: {str(e)})"
