## passive_income_generator/asgi.py

"""
ASGI config for passive_income_generator project.

It exposes the ASGI callable as a module-level variable named `application`.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

# Import your WebSocket consumer here
from income_streams.consumers import IncomeStreamConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'passive_income_generator.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Define WebSocket URL patterns
websocket_urlpatterns = [
    path('ws/income-streams/', IncomeStreamConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
