"""
Serviço de cobrança - Gerencia criação de cobranças e lógica de negócio.
Seguindo Single Responsibility: apenas operações relacionadas a cobrança.
"""
from typing import Optional
from decimal import Decimal
from django.utils import timezone
from datetime import date, timedelta

from cobranca_app.models import Cliente, Cobranca, Plano
from cobranca_app.core.constantes import (
    StatusCobranca,
    FORMATO_DATA_REFERENCIA,
    DIAS_POR_MES,
    DIAS_ANTES_VENCIMENTO_LEMBRETE,
    DIAS_APOS_VENCIMENTO_AVISO_1,
    DIAS_APOS_VENCIMENTO_AVISO_2
)
from cobranca_app.core.utilitarios import calcular_data_vencimento, registrar_evento
from cobranca_app.core.excecoes import ExcecaoCobrancaOperacao


class ServicoCobranca:
    """Serviço para gerenciar cobranças."""
    
    @staticmethod
    def criar_cobranca_inicial(cliente: Cliente) -> Cobranca:
        """
        Cria a primeira cobrança para um novo cliente.
        
        Args:
            cliente: Instância do cliente
        
        Returns:
            Instância de Cobranca criada
        
        Raises:
            ExcecaoCobrancaOperacao: Se a criação da cobrança falhar
        """
        if not cliente.plano:
            raise ExcecaoCobrancaOperacao("Cliente deve ter um plano para criar cobrança")
        
        try:
            data_vencimento = cliente.calcular_proxima_data_vencimento()
            valor_base = cliente.plano.valor_base
            
            return Cobranca.objects.create(
                cliente=cliente,
                valor_base=valor_base,
                valor_multa_juros=Decimal('0.00'),
                valor_total_devido=valor_base,
                data_vencimento=data_vencimento,
                referencia_ciclo=data_vencimento.strftime(FORMATO_DATA_REFERENCIA),
                status_cobranca=StatusCobranca.PENDENTE.value
            )
        except Exception as e:
            registrar_evento("error", "Falha ao criar cobrança inicial", cliente_cpf=cliente.cpf)
            raise ExcecaoCobrancaOperacao(f"Erro ao criar cobrança: {e}") from e
    
    @staticmethod
    def marcar_cobrancas_atrasadas() -> int:
        """
        Marca cobranças pendentes como atrasadas se passaram da data de vencimento.
        
        Returns:
            Número de cobranças marcadas como atrasadas
        """
        hoje = timezone.localdate()
        cobrancas_atrasadas = Cobranca.objects.filter(
            status_cobranca=StatusCobranca.PENDENTE.value,
            data_vencimento__lt=hoje
        )
        
        count = cobrancas_atrasadas.count()
        for cobranca in cobrancas_atrasadas:
            cobranca.marcar_como_atrasado()
        
        return count
    
    @staticmethod
    def obter_cobrancas_para_lembrete(data_lembrete: date) -> list:
        """
        Obtém cobranças que precisam de notificação de lembrete.
        
        Args:
            data_lembrete: Data para verificar lembretes
        
        Returns:
            Lista de instâncias de Cobranca
        """
        return list(
            Cobranca.objects.filter(
                status_cobranca=StatusCobranca.PENDENTE.value,
                data_vencimento=data_lembrete
            ).select_related('cliente')
        )
    
    @staticmethod
    def obter_cobrancas_atrasadas() -> list:
        """
        Obtém todas as cobranças atrasadas.
        
        Returns:
            Lista de instâncias de Cobranca atrasadas
        """
        return list(
            Cobranca.objects.filter(
                status_cobranca=StatusCobranca.ATRASADO.value
            ).select_related('cliente')
        )

