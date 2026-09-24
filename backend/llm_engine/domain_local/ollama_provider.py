"""
Ollama Local LLM Provider
Connects to a locally-running Ollama instance (http://localhost:11434).
Model: llama3.2 (or whatever is configured via OLLAMA_MODEL env var).
"""
import os
import json
import logging
import requests

from llm_engine.interfaces import LLMProvider

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.2")
DEFAULT_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT_SEC", "120"))


class OllamaProvider(LLMProvider):
    """
    LLM provider that talks to a local Ollama server via its HTTP API.
    Uses /api/chat with streaming disabled for simplicity.
    """

    def __init__(self, model: str = None, base_url: str = None, timeout: int = None):
        self.model    = model    or OLLAMA_MODEL
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.timeout  = timeout  or DEFAULT_TIMEOUT
        logger.info(f"[OllamaProvider] Using model={self.model} at {self.base_url}")

    # ─────────────────────────────────────────────────────────────────────────
    def generate_response(
        self,
        prompt: str,
        system_instruction: str = None,
        timeout: int = None,
    ) -> str:
        """
        Send a chat request to Ollama and return the assistant's reply as a string.
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model":  self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048,
            },
        }

        t = timeout or self.timeout
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=t,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            if not text:
                raise ValueError(f"Ollama returned empty content: {data}")
            logger.info(f"[OllamaProvider] Response: {len(text)} chars")
            return text

        except requests.exceptions.ConnectionError:
            msg = (
                f"Cannot reach Ollama at {self.base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )
            logger.error(f"[OllamaProvider] {msg}")
            raise RuntimeError(msg)

        except requests.exceptions.Timeout:
            msg = f"Ollama request timed out after {t}s"
            logger.error(f"[OllamaProvider] {msg}")
            raise RuntimeError(msg)

        except Exception as e:
            logger.error(f"[OllamaProvider] Error: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    def generate_vision_response(
        self,
        prompt: str,
        image_base64: str,
        system_instruction: str = None,
    ) -> str:
        """
        Send a vision request to Ollama (multimodal models like llava, llama3.2-vision).
        Falls back to text-only if the model doesn't support images.
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        # Ollama accepts images as a list of base64 strings in the message
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_base64],
        })

        payload = {
            "model":  self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 2048},
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            logger.info(f"[OllamaProvider] Vision response: {len(text)} chars")
            return text or "No response from model."

        except Exception as e:
            logger.warning(f"[OllamaProvider] Vision request failed ({e}), falling back to text-only")
            return self.generate_response(prompt, system_instruction)
