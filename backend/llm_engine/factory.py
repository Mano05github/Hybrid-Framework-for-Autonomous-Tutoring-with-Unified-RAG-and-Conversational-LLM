"""
LLM Factory — routes to the active provider.
Currently supports:
  - gemini (Google's Gemini 2.5 API, recommended)
  - ollama (Local models)
  - qwen   (OpenRouter)
"""
import os
import logging

logger = logging.getLogger(__name__)


class LLMFactory:
    @staticmethod
    def get_provider():
        """
        Returns the active LLM provider based on LLM_PROVIDER in .env.
        """
        provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

        if provider == "gemini":
            from llm_engine.domain_gemini.gemini_provider import GeminiProvider
            logger.info("LLMFactory: Using Gemini API (gemini-2.5-flash)")
            return GeminiProvider()

        elif provider == "ollama":
            from llm_engine.domain_local.ollama_provider import OllamaProvider
            model = os.getenv("OLLAMA_MODEL", "llama3.2")
            logger.info(f"LLMFactory: Using Ollama ({model})")
            return OllamaProvider(model=model)

        elif provider == "qwen":
            from llm_engine.domain_qwen.qwen_provider import QwenProvider
            logger.info("LLMFactory: Using Qwen via OpenRouter")
            return QwenProvider()

        else:
            logger.warning(
                f"LLMFactory: Unknown provider '{provider}', defaulting to Gemini"
            )
            from llm_engine.domain_gemini.gemini_provider import GeminiProvider
            return GeminiProvider()
