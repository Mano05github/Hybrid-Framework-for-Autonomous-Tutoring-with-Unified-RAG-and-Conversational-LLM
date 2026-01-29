import requests
import logging
import json
from llm_engine.interfaces import LLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        logger.info(f"Initialized Ollama Provider with model: {self.model_name}")

    def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        try:
            # Construct the payload
            # Ollama supports 'system' parameter in generate endpoint
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,  # Non-streaming for simplicity in Phase 1
            }
            
            if system_instruction:
                payload["system"] = system_instruction
            else:
                 payload["system"] = "You are a wise Socratic Tutor for Computer Science. Guide the student by asking questions, not just giving answers. Be concise."

            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"Ollama Error {response.status_code}: {response.text}")
                return f"Local Brain Error: {response.text}"

        except requests.exceptions.ConnectionError:
             logger.error("Failed to connect to Ollama. Is it running?")
             return "I cannot reach my local brain. Please ensure Ollama is running at port 11434."
        except Exception as e:
            logger.error(f"Ollama Generation Failed: {e}")
            return f"I'm sorry, I'm having trouble thinking locally. (Error: {str(e)})"

    def generate_vision_response(self, prompt: str, image_base64: str, system_instruction: str = None) -> str:
        try:
            # Llama 3.2 Vision uses the same 'generate' endpoint but with 'images' field
            payload = {
                "model": self.model_name, # e.g. "llama3.2-vision"
                "prompt": prompt,
                "stream": False,
                "images": [image_base64] # Expects list of base64 strings
            }

            if system_instruction:
                payload["system"] = system_instruction
            else:
                payload["system"] = "You are a Helpful Vision Assistant. Analyze the image provided."

            response = requests.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"Ollama Vision Error {response.status_code}: {response.text}")
                return f"Vision Error: {response.text}"
        except Exception as e:
            logger.error(f"Ollama Vision Failed: {e}")
            return f"I cannot see right now. (Error: {str(e)})"
