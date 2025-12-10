"""
API Views for the billing application.
Following Clean Code: views only handle HTTP requests/responses, business logic in services.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from cobranca_app.models import Plano, Cliente, Cobranca, Notificacao
from cobranca_app.serializers import (
    PlanoSerializer,
    ClienteSerializer,
    CobrancaSerializer,
    NotificacaoSerializer
)
from cobranca_app.services.servico_cliente import ServicoCliente
from cobranca_app.core.constantes import StatusCobranca
from cobranca_app.core.excecoes import ExcecaoCliente, ExcecaoCobrancaOperacao


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
        try:
            cliente = serializer.save()
            ServicoCliente.criar_cliente_com_cobranca_inicial(cliente)
        except Exception as e:
            # Re-raise para que o exception handler possa tratar
            raise
        

class CobrancaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing billings.
    Handles listing and payment marking operations.
    """
    queryset = Cobranca.objects.all().select_related('cliente').order_by('-data_vencimento')
    serializer_class = CobrancaSerializer
    
    def get_queryset(self):
        """
        Filtra as cobranças por status se o parâmetro 'status' for fornecido.
        """
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status', None)
        
        if status_param:
            queryset = queryset.filter(status_cobranca=status_param.upper())
        
        return queryset
    
    def update(self, request, *args, **kwargs):
        """
        Atualiza uma cobrança (permite reverter pagamento).
        
        Permite atualizar status_cobranca e data_pagamento para reverter pagamento.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Se estiver revertendo pagamento (status_cobranca para PENDENTE e data_pagamento null)
        if 'status_cobranca' in request.data and request.data['status_cobranca'] in ['PENDENTE', 'ATRASADO']:
            if 'data_pagamento' in request.data and request.data['data_pagamento'] is None:
                instance.data_pagamento = None
        
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def atrasadas(self, request) -> Response:
        """
        Retorna todas as cobranças atrasadas.
        
        Returns:
            Lista de cobranças com status ATRASADO
        """
        cobrancas_atrasadas = self.get_queryset().filter(
            status_cobranca=StatusCobranca.ATRASADO.value
        )
        serializer = self.get_serializer(cobrancas_atrasadas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request) -> Response:
        """
        Retorna todas as cobranças pendentes.
        
        Returns:
            Lista de cobranças com status PENDENTE
        """
        cobrancas_pendentes = self.get_queryset().filter(
            status_cobranca=StatusCobranca.PENDENTE.value
        )
        serializer = self.get_serializer(cobrancas_pendentes, many=True)
        return Response(serializer.data)
    
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


class NotificacaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing notifications.
    Read-only endpoint for viewing all notifications sent by the system.
    """
    queryset = Notificacao.objects.all().select_related(
        'cobranca__cliente'
    ).order_by('-data_agendada')
    serializer_class = NotificacaoSerializer
