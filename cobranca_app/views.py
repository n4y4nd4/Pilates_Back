# cobranca_app/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Plano, Cliente, Cobranca
from .serializers import PlanoSerializer, ClienteSerializer, CobrancaSerializer
from django.utils import timezone
from datetime import timedelta


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, criar, atualizar e deletar Clientes.
    Usado para o Wireframe de Cadastro e Listagem de Clientes.
    """
    queryset = Cliente.objects.all().order_by('nome')
    serializer_class = ClienteSerializer
    
    def perform_create(self, serializer):
        cliente = serializer.save()
        
        periodicidade = cliente.plano.periodicidade_meses
        data_vencimento = cliente.data_inicio_contrato + timedelta(days=periodicidade * 30) 
        
        Cobranca.objects.create(
            cliente=cliente,
            valor_base=cliente.plano.valor_base,
            valor_total_devido=cliente.plano.valor_base,
            data_vencimento=data_vencimento,
            referencia_ciclo=data_vencimento.strftime("%Y-%m") 
        )
        

class CobrancaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar Cobranças e realizar a ação de Marcar como Pago.
    Usado para o Wireframe de Listagem de Cobranças.
    """
    queryset = Cobranca.objects.all().order_by('-data_vencimento')
    serializer_class = CobrancaSerializer
    
    @action(detail=True, methods=['patch'])
    def marcar_pago(self, request, pk=None):
        cobranca = self.get_object()
        
        if cobranca.status_cobranca == 'PAGO':
            return Response({'status': 'Cobrança já está paga'}, status=200)

        cobranca.status_cobranca = 'PAGO'
        cobranca.data_pagamento = timezone.localdate()
        cobranca.valor_multa_juros = 0.00 
        cobranca.save()
        
        return Response(CobrancaSerializer(cobranca).data)


class PlanoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar os Planos disponíveis (usado no dropdown do Cadastro).
    """
    queryset = Plano.objects.all().filter(ativo=True)
    serializer_class = PlanoSerializer