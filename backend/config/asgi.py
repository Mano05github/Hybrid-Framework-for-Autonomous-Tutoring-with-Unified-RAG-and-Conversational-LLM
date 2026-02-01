"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import learning_session.routing 

# Warm up Ollama in background
from llm_engine.warmup import warmup_ollama_async, check_ollama_health

# Check Ollama health and start warmup
is_healthy, models = check_ollama_health()
if is_healthy:
    print(f"✅ Ollama is running with models: {models}")
    warmup_ollama_async()
else:
    print("⚠️ Ollama is not running. Start it with 'ollama serve'")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            learning_session.routing.websocket_urlpatterns
        )
    ),
})
