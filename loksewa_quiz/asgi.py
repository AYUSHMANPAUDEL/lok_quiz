import os
import django

# Ensure Django initializes before anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loksewa_quiz.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import home.routing  # Adjust this import based on your app name

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            home.routing.websocket_urlpatterns
        )
    ),
})
