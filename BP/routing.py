from django.urls import path
from . import consumers

websockets_urlspatterns = [
    path('BP/chat/<client_id>/<case_id>/', consumers.ChatConsumer.as_asgi())
]