import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from mychat.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mychat.settings')

application = ProtocolTypeRouter(
   {
      'http': get_asgi_application(),
      'websocket': AllowedHostsOriginValidator(
         AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
      )
   }
)
