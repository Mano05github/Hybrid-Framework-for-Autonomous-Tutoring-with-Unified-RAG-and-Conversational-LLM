import atexit
import logging
import os
import subprocess
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)

_neutts_process = None


class LearningSessionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning_session'

    def ready(self):
        if os.environ.get("NEUTTS_AUTOSTART", "1") != "1":
            return

        if "runserver" not in sys.argv:
            return

        if os.environ.get("RUN_MAIN") != "true":
            return

        self._ensure_neutts_service()

    def _ensure_neutts_service(self):
        global _neutts_process

        service_url = os.getenv("NEUTTS_SERVICE_URL", "http://127.0.0.1:8755/tts")
        health_url = service_url.replace("/tts", "/health")

        if self._is_service_healthy(health_url):
            logger.info("NeuTTS service already running: %s", service_url)
            return

        host = os.getenv("NEUTTS_SERVICE_HOST", "127.0.0.1")
        port = os.getenv("NEUTTS_SERVICE_PORT", "8755")

        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "learning_session.neutts_air_app:app",
            "--host",
            host,
            "--port",
            str(port),
        ]

        try:
            _neutts_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            atexit.register(self._stop_neutts_service)
            logger.info("Started NeuTTS service: %s", " ".join(command))
        except Exception as exc:
            logger.error("Failed to start NeuTTS service: %s", exc)

    def _is_service_healthy(self, health_url: str) -> bool:
        try:
            import requests

            response = requests.get(health_url, timeout=1.0)
            return response.status_code == 200
        except Exception:
            return False

    def _stop_neutts_service(self):
        global _neutts_process

        if _neutts_process and _neutts_process.poll() is None:
            _neutts_process.terminate()
            _neutts_process = None
