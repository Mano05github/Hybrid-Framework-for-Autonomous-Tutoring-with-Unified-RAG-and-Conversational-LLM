"""
Ollama warmup utilities to reduce first-request latency
"""
import requests
import logging
from threading import Thread
import time

logger = logging.getLogger(__name__)


def warmup_ollama(model_name="llama3.2", api_url="http://localhost:11434"):
    """
    Warm up Ollama by sending a simple test request.
    This loads the model into memory, reducing latency for subsequent requests.
    
    Args:
        model_name: Name of the model to warm up
        api_url: Ollama API endpoint
    """
    try:
        # Test health endpoint first
        health_response = requests.get(f"{api_url}/api/tags", timeout=2)
        
        if health_response.status_code != 200:
            logger.warning(f"Ollama health check failed: {health_response.status_code}")
            return False
        
        logger.info(f"🔥 Warming up Ollama model: {model_name}")
        
        # Send a tiny warmup request
        warmup_payload = {
            "model": model_name,
            "prompt": "Hi",
            "stream": False,
            "options": {
                "num_predict": 5  # Just 5 tokens to make it fast
            }
        }
        
        response = requests.post(
            f"{api_url}/api/generate",
            json=warmup_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Ollama warmup successful for {model_name}")
            return True
        else:
            logger.warning(f"⚠️ Ollama warmup returned {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.warning(f"⚠️ Ollama warmup timed out (model may be loading)")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Cannot connect to Ollama at {api_url}")
        return False
    except Exception as e:
        logger.error(f"❌ Ollama warmup error: {e}")
        return False


def warmup_ollama_async(model_name="llama3.2", api_url="http://localhost:11434"):
    """
    Asynchronously warm up Ollama in a background thread.
    This doesn't block server startup.
    """
    def _warmup():
        time.sleep(2)  # Wait 2 seconds for server to fully start
        warmup_ollama(model_name, api_url)
    
    thread = Thread(target=_warmup, daemon=True)
    thread.start()
    logger.info("🔥 Started Ollama warmup in background")


def check_ollama_health(api_url="http://localhost:11434"):
    """
    Check if Ollama is running and responsive.
    
    Returns:
        tuple: (is_healthy: bool, available_models: list)
    """
    try:
        response = requests.get(f"{api_url}/api/tags", timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            return True, models
        else:
            return False, []
            
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return False, []
