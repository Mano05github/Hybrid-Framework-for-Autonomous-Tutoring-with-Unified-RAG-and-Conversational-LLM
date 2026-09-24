"""
Gemini API Provider
Connects to Google's Gemini models using the modern google-genai SDK.
"""
import os
import logging
import base64

from google import genai
from google.genai import types

from llm_engine.interfaces import LLMProvider

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class GeminiProvider(LLMProvider):
    """
    LLM provider that talks to Google's Gemini API via google-genai.
    """

    def __init__(self, model: str = None):
        self.model = model or GEMINI_MODEL
        
        if not GEMINI_API_KEY:
            logger.warning("[GeminiProvider] GOOGLE_API_KEY is not set in environment.")
            
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        logger.info(f"[GeminiProvider] Using model={self.model}")

    # ─────────────────────────────────────────────────────────────────────────
    def generate_response(
        self,
        prompt: str,
        system_instruction: str = None,
        timeout: int = None, # Timeout not strictly used in identical way by genai SDK but kept for signature
    ) -> str:
        """
        Send a text request to Gemini and return the assistant's reply.
        """
        if not self.client:
            msg = "GOOGLE_API_KEY is missing. Cannot call Gemini API."
            logger.error(f"[GeminiProvider] {msg}")
            raise RuntimeError(msg)

        try:
            config_kwargs = {}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
                
            config = types.GenerateContentConfig(**config_kwargs)

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            text = response.text
            if not text:
                logger.warning("[GeminiProvider] Gemini returned empty content.")
                return ""
                
            logger.info(f"[GeminiProvider] Response: {len(text)} chars")
            return text

        except Exception as e:
            logger.error(f"[GeminiProvider] Error: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    def generate_vision_response(
        self,
        prompt: str,
        image_base64: str,
        system_instruction: str = None,
    ) -> str:
        """
        Send a vision request to Gemini.
        """
        if not self.client:
            msg = "GOOGLE_API_KEY is missing. Cannot call Gemini API."
            logger.error(f"[GeminiProvider] {msg}")
            raise RuntimeError(msg)

        try:
            # The new SDK handles base64 natively through types.Part.from_bytes
            # Remove data URI scheme if present
            if image_base64.startswith("data:"):
                # Format: data:image/jpeg;base64,/9j/4AAQSkZ...
                header, base64_data = image_base64.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
            else:
                base64_data = image_base64
                mime_type = "image/jpeg" # Assume JPEG if no header

            image_bytes = base64.b64decode(base64_data)
            
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )

            config_kwargs = {}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
                
            config = types.GenerateContentConfig(**config_kwargs)

            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, image_part],
                config=config
            )

            text = response.text
            logger.info(f"[GeminiProvider] Vision response: {len(text)} chars")
            return text or "No response from model."

        except Exception as e:
            logger.error(f"[GeminiProvider] Vision request failed: {e}")
            # Do not fallback to text-only if vision fails, as the image was likely crucial
            raise RuntimeError(f"Gemini Vision Error: {e}")
