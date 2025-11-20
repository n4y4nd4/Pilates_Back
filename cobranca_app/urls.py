# cobranca_app/urls.py

from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, CobrancaViewSet, PlanoViewSet, NotificacaoViewSet
from django.urls import path, include

# 1. Cria um Router (Gerenciador de URLs do DRF)
router = DefaultRouter()

# 2. Registra os ViewSets (Isso cria automaticamente URLs como /clientes/, /clientes/1/, etc.)
router.register(r'clientes', ClienteViewSet)
router.register(r'cobrancas', CobrancaViewSet)
router.register(r'planos', PlanoViewSet)
router.register(r'notificacoes', NotificacaoViewSet)

# 3. Define as URLs da API
urlpatterns = [
    path('', include(router.urls)),
]