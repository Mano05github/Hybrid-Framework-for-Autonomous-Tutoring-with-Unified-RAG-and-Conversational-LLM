"""
Qwen LLM Provider via OpenRouter
==================================
Uses OpenRouter's OpenAI-compatible API to call:
  qwen/qwen3-next-80b-a3b-instruct:free

OpenRouter endpoint: https://openrouter.ai/api/v1/chat/completions
Auth: Bearer sk-or-v1-...
"""
import os
import logging
import requests
from llm_engine.interfaces import LLMProvider

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3-32b"   # Free on OpenRouter ($0 per token)


class QwenProvider(LLMProvider):
    """
    LLM provider backed by Qwen via OpenRouter.
    Compatible with the same interface as OllamaProvider and GoogleGeminiProvider.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment variables.")

        self.model = os.getenv("QWEN_MODEL", DEFAULT_MODEL)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",   # Required by OpenRouter
            "X-Title": "Vaathiyar AI Tutor",           # Optional but good practice
        }
        logger.info(f"✅ Qwen Provider initialized — model: {self.model}")

    def generate_response(
        self,
        prompt: str,
        system_instruction: str = None,
        timeout: int = 60,          # seconds; Qwen API is fast, 60s is very generous
        **kwargs
    ) -> str:
        """
        Generate a text response from Qwen.

        Args:
            prompt:             The user's query / input text.
            system_instruction: System/context instruction (teacher prompt, RAG context, etc.)
            timeout:            Max seconds to wait for the API (passed but rarely triggered).

        Returns:
            Generated text string.
        """
        if not system_instruction:
            system_instruction = (
                "You are a wise Socratic Tutor for Computer Science. "
                "Guide the student by asking questions, not just giving answers. Be concise."
            )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user",   "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": kwargs.get("temperature", 0.7),  # Per-call override
        }

        try:
            response = requests.post(
                OPENROUTER_BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )

            # --- Retry once on transient server errors ---
            if response.status_code in (429, 503):
                import time as _time
                logger.warning(f"Qwen returned {response.status_code} — retrying in 3s...")
                _time.sleep(3)
                response = requests.post(
                    OPENROUTER_BASE_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=timeout,
                )

            response.raise_for_status()

            data = response.json()
            text = data["choices"][0]["message"]["content"]

            # Log performance metrics if available
            usage = data.get("usage", {})
            logger.info(
                f"✅ Qwen: {usage.get('total_tokens', '?')} tokens used "
                f"(prompt={usage.get('prompt_tokens','?')}, "
                f"completion={usage.get('completion_tokens','?')})"
            )
            return text

        except requests.exceptions.Timeout:
            logger.error(f"Qwen API timeout after {timeout}s")
            raise TimeoutError(f"Qwen API did not respond within {timeout}s.")

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            body = e.response.text[:300] if e.response else ""
            logger.error(f"Qwen HTTP {status}: {body}")
            # Re-raise so calling agents can choose their own fallback message
            raise RuntimeError(f"Qwen API error (HTTP {status})")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot reach OpenRouter API: {e}")
            raise RuntimeError("Cannot reach OpenRouter API — check internet connection.")

        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Qwen response format: {e}")
            raise RuntimeError("Unexpected response format from Qwen.")

        except Exception as e:
            logger.error(f"Qwen generation failed: {e}")
            raise

    def generate_vision_response(
        self,
        prompt: str,
        image_base64: str,
        system_instruction: str = None,
        **kwargs
    ) -> str:
        """
        Vision stub — Qwen free tier is text-only.
        Falls back to text-only analysis with a note.
        """
        logger.warning("Qwen free tier does not support vision. Using text-only fallback.")
        text_prompt = (
            f"[Note: I cannot see the image directly, but based on context:]\n{prompt}"
        )
        return self.generate_response(
            prompt=text_prompt,
            system_instruction=system_instruction or "You are a helpful diagram analysis assistant.",
        )
