import atexit
import logging
import os
import subprocess
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)

_redis_process = None


class AiEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_engine'
    
    def ready(self):
        """Models load lazily on first use (cached locally)."""
        if os.environ.get("REDIS_AUTOSTART", "1") != "1":
            return

        if os.environ.get("CACHE_MODE", "memory").lower() != "redis":
            return

        if "runserver" not in sys.argv:
            return

        if os.environ.get("RUN_MAIN") != "true":
            return

        self._ensure_redis()

    def _ensure_redis(self):
        global _redis_process

        host = os.getenv("REDIS_HOST", "127.0.0.1")
        port = int(os.getenv("REDIS_PORT", "6379"))

        if self._is_redis_ready(host, port):
            logger.info("Redis already running at %s:%s", host, port)
            return

        command = ["redis-server", "--bind", host, "--port", str(port)]

        try:
            _redis_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            atexit.register(self._stop_redis)
            logger.info("Started Redis: %s", " ".join(command))
        except Exception as exc:
            logger.error("Failed to start Redis: %s", exc)

    def _is_redis_ready(self, host: str, port: int) -> bool:
        try:
            import redis

            client = redis.Redis(host=host, port=port, db=0)
            client.ping()
            return True
        except Exception:
            return False

    def _stop_redis(self):
        global _redis_process

        if _redis_process and _redis_process.poll() is None:
            _redis_process.terminate()
            _redis_process = None
