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
from cobranca_app.core.constantes import StatusCobranca, StatusEnvio
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
    
    @action(detail=False, methods=['get'])
    def proximos_vencimentos(self, request) -> Response:
        """
        Retorna as próximas cobranças a vencer (pendentes próximas do vencimento).
        Retorna cobranças com status PENDENTE ordenadas por data de vencimento.
        
        Returns:
            Lista de cobranças pendentes ordenadas por data de vencimento
        """
        from django.utils import timezone
        cobrancas = self.get_queryset().filter(
            status_cobranca=StatusCobranca.PENDENTE.value
        ).order_by('data_vencimento')
        serializer = self.get_serializer(cobrancas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pagamentos_atrasados(self, request) -> Response:
        """
        Retorna todos os pagamentos atrasados (com status ATRASADO).
        
        Returns:
            Lista de cobranças com status ATRASADO ordenadas por data de vencimento
        """
        cobrancas_atrasadas = self.get_queryset().filter(
            status_cobranca=StatusCobranca.ATRASADO.value
        ).order_by('data_vencimento')
        serializer = self.get_serializer(cobrancas_atrasadas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def agendadas_para_envio(self, request) -> Response:
        """
        Retorna cobranças PENDENTES que serão notificadas (próximas de vencer).
        
        Returns:
            Lista de cobranças pendentes que estão elegíveis para notificação
        """
        from django.utils import timezone
        from datetime import timedelta
        from cobranca_app.core.constantes import DIAS_ANTES_VENCIMENTO_LEMBRETE
        
        hoje = timezone.localdate()
        data_lembrete = hoje + timedelta(days=DIAS_ANTES_VENCIMENTO_LEMBRETE)
        
        cobrancas_agendadas = self.get_queryset().filter(
            status_cobranca=StatusCobranca.PENDENTE.value,
            data_vencimento=data_lembrete
        ).order_by('data_vencimento')
        
        serializer = self.get_serializer(cobrancas_agendadas, many=True)
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
    
    def get_queryset(self):
        """
        Filtra notificações por status se o parâmetro 'status' for fornecido.
        """
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status', None)
        
        if status_param:
            queryset = queryset.filter(status_envio=status_param.upper())
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def enviadas(self, request) -> Response:
        """
        Retorna todas as notificações enviadas com sucesso.
        
        Returns:
            Lista de notificações com status ENVIADO
        """
        from cobranca_app.core.constantes import StatusEnvio
        notificacoes = self.get_queryset().filter(
            status_envio=StatusEnvio.ENVIADO.value
        )
        serializer = self.get_serializer(notificacoes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def agendadas(self, request) -> Response:
        """
        Retorna:
        1. Notificações com status AGENDADO (já criadas no banco)
        2. Cobranças PENDENTES que serão notificadas no próximo disparo (próximas de vencer em 7 dias)
        
        Simula quais emails estão agendados para envio futuro.
        
        Returns:
            Lista de notificações agendadas + cobranças pendentes elegíveis
        """
        from django.utils import timezone
        from datetime import timedelta
        from cobranca_app.core.constantes import DIAS_ANTES_VENCIMENTO_LEMBRETE, StatusCobranca
        
        # 1. Notificações já criadas com status AGENDADO
        notificacoes = self.get_queryset().filter(
            status_envio=StatusEnvio.AGENDADO.value
        )
        notif_serializer = self.get_serializer(notificacoes, many=True)
        notif_data = notif_serializer.data
        
        # 2. Cobranças PENDENTES elegíveis para envio (próximas de vencer em DIAS_ANTES_VENCIMENTO_LEMBRETE dias)
        #    Mostrar apenas UMA cobrança por cliente (a mais próxima) para evitar múltiplas linhas
        hoje = timezone.localdate()
        data_lembrete = hoje + timedelta(days=DIAS_ANTES_VENCIMENTO_LEMBRETE)

        # Buscar cobranças pendentes no intervalo [hoje, data_lembrete] e ordenar por cliente + vencimento
        cobrancas_qs = Cobranca.objects.filter(
            status_cobranca=StatusCobranca.PENDENTE.value,
            data_vencimento__gte=hoje,
            data_vencimento__lte=data_lembrete
        ).select_related('cliente').order_by('cliente__cpf', 'data_vencimento')

        # Deduplicar por cliente (pegar a cobrança mais próxima por cliente)
        seen_cpfs = set()
        cobrancas_dedup = []
        for c in cobrancas_qs:
            cpf = getattr(c.cliente, 'cpf', None)
            if cpf in seen_cpfs:
                continue
            seen_cpfs.add(cpf)
            cobrancas_dedup.append(c)

        # Converter cobranças pendentes deduplicadas em formato de notificação para apresentação uniforme
        cobranca_serializer = CobrancaSerializer(cobrancas_dedup, many=True)

        # Criar representação de "notificações agendadas" a partir das cobranças pendentes
        cobr_as_notif = []
        for cobr_data in cobranca_serializer.data:
            cobr_as_notif.append({
                "id": None,  # Notificação ainda não foi criada
                "cliente_nome": cobr_data.get('cliente_nome'),
                "cliente_email": cobr_data.get('cliente_email'),
                "cobranca_referencia": cobr_data.get('referencia_ciclo'),
                "cobranca_valor": cobr_data.get('valor_total_devido'),
                "cobranca_data_vencimento": cobr_data.get('data_vencimento'),
                "dias_em_atraso": 0,  # Ainda não atrasada
                "status_envio": "AGENDADO",
                "tipo_regua": "Lembrete de Vencimento",
                "tipo_canal": "Email",
                "data_agendada": str(hoje),
            })
        
        # Combinar notificações já criadas com as cobranças pendentes agendadas
        resultado = notif_data + cobr_as_notif
        
        return Response(resultado)

    
    @action(detail=False, methods=['get'])
    def com_falha(self, request) -> Response:
        """
        Retorna todas as notificações que falharam ao enviar.
        
        Returns:
            Lista de notificações com status FALHA
        """
        from cobranca_app.core.constantes import StatusEnvio
        notificacoes = self.get_queryset().filter(
            status_envio=StatusEnvio.FALHA.value
        )
        serializer = self.get_serializer(notificacoes, many=True)
        return Response(serializer.data)
