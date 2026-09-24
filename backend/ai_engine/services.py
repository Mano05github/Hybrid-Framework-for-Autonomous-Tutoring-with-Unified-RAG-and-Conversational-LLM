import os
from google import genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Initialize centralized Gemini client
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
