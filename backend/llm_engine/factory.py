import os
import logging
from .domain_gemini.gemini_provider import GoogleGeminiProvider
from .domain_local.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class LLMFactory:
    @staticmethod
    def get_provider():
        # Read config (Default to local to save credits)
        mode = os.getenv("AI_ENGINE_MODE", "local_llama")
        
        logger.info(f"LLM Factory initializing mode: {mode}")

        if mode == "google_gemini":
            return GoogleGeminiProvider()
        elif mode == "local_llama" or mode == "local_mistral":
            # flexible naming, both map to OllamaProvider default
            return OllamaProvider(model_name="llama3.2")
        else:
            logger.warning(f"Unknown AI_ENGINE_MODE '{mode}', defaulting to Local Llama")
            return OllamaProvider(model_name="llama3.2")
