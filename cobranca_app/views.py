"""
API Views for the billing application.
Following Clean Code: views only handle HTTP requests/responses, business logic in services.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from cobranca_app.models import Plano, Cliente, Cobranca
from cobranca_app.serializers import (
    PlanoSerializer,
    ClienteSerializer,
    CobrancaSerializer
)
from cobranca_app.services.cliente_service import ClienteService
from cobranca_app.core.constants import StatusCobranca
from cobranca_app.core.exceptions import ClienteException, CobrancaException


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clients.
    Handles CRUD operations via REST API.
    """
    queryset = Cliente.objects.all().order_by('nome')
    serializer_class = ClienteSerializer
    
    def perform_create(self, serializer) -> None:
        """
        Create a new client and automatically generate first billing.
        
        Args:
            serializer: ClienteSerializer instance
        """
        cliente = serializer.save()
        ClienteService.create_client_with_initial_billing(cliente)


class CobrancaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing billings.
    Handles listing and payment marking operations.
    """
    queryset = Cobranca.objects.all().order_by('-data_vencimento')
    serializer_class = CobrancaSerializer
    
    @action(detail=True, methods=['patch'])
    def marcar_pago(self, request, pk=None) -> Response:
        """
        Mark a billing as paid.
        
        Args:
            request: HTTP request
            pk: Billing primary key
        
        Returns:
            HTTP response with billing data or error message
        """
        cobranca = self.get_object()
        
        if cobranca.is_pago():
            return Response(
                {'status': 'Cobrança já está paga'},
                status=status.HTTP_200_OK
            )
        
        try:
            cobranca.marcar_como_pago()
            return Response(
                CobrancaSerializer(cobranca).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao marcar como pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlanoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing available service plans.
    Read-only endpoint for plan selection in client registration.
    """
    queryset = Plano.objects.filter(ativo=True).order_by('nome_plano')
    serializer_class = PlanoSerializer
