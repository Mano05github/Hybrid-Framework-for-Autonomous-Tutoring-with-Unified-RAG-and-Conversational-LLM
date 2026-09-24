"""
LLM health check — Qwen via OpenRouter
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)


def check_qwen_health() -> bool:
    """
    Verify OpenRouter is reachable and the API key is valid.
    HTTP 429 (rate limit) still counts as healthy — the key works.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.error("❌ OPENROUTER_API_KEY not set")
        return False

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("QWEN_MODEL", "qwen/qwen3-next-80b-a3b-instruct:free"),
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1,
            },
            timeout=10,
        )
        if response.status_code == 200:
            logger.info("✅ Qwen (OpenRouter) is reachable and API key is valid")
            return True
        elif response.status_code == 429:
            # Rate limited but key and endpoint are valid — treat as healthy
            logger.info("✅ Qwen (OpenRouter) API key valid (rate-limited on probe, queries will work)")
            return True
        else:
            logger.warning(f"⚠️ OpenRouter returned HTTP {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        logger.error(f"❌ Qwen health check failed: {e}")
        return False


# Backwards-compat stubs (used in settings.py startup checks)
def warmup_ollama(*args, **kwargs):
    logger.info("ℹ️  warmup_ollama: Ollama removed. Using Qwen via OpenRouter.")

def warmup_ollama_async(*args, **kwargs):
    check_qwen_health()

def check_ollama_health(*args, **kwargs):
    ok = check_qwen_health()
    models = ["qwen/qwen3-next-80b-a3b-instruct:free"] if ok else []
    return ok, models
