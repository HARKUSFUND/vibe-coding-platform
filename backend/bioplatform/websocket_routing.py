"""
WebSocket routing configuration for bioplatform.
"""

from django.urls import re_path
from bioplatform.astm_connector.consumers import ASTMConsumer
from bioplatform.resultats.consumers import ResultatConsumer

websocket_urlpatterns = [
    re_path(r'ws/astm/$', ASTMConsumer.as_asgi()),
    re_path(r'ws/resultats/$', ResultatConsumer.as_asgi()),
]
