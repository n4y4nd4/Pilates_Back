"""
Message builder service - Creates notification messages.
Following Single Responsibility: only message content creation.
"""
from typing import Tuple
from datetime import date

from cobranca_app.models import Cobranca, Cliente
from cobranca_app.core.constants import (
    DAYS_BEFORE_DUE_REMINDER,
    DAYS_AFTER_DUE_WARNING_1,
    DAYS_AFTER_DUE_WARNING_2
)


class MessageBuilder:
    """Service for building notification messages."""
    
    @staticmethod
    def build_reminder_message(cobranca: Cobranca) -> Tuple[str, str]:
        """
        Build reminder message (D-3).
        
        Args:
            cobranca: Billing instance
        
        Returns:
            Tuple of (tipo_regua, message_content)
        """
        cliente = cobranca.cliente
        tipo_regua = 'Lembrete (D-3)'
        conteudo = (
            f"Olá {cliente.nome}, sua cobrança de R$ {cobranca.valor_total_devido} "
            f"vencerá em 3 dias ({cobranca.data_vencimento.strftime('%d/%m/%Y')})."
        )
        return tipo_regua, conteudo
    
    @staticmethod
    def build_overdue_message(cobranca: Cobranca, days_overdue: int) -> Tuple[str, str]:
        """
        Build overdue message based on days overdue.
        
        Args:
            cobranca: Billing instance
            days_overdue: Number of days overdue
        
        Returns:
            Tuple of (tipo_regua, message_content)
        """
        cliente = cobranca.cliente
        
        if days_overdue == DAYS_AFTER_DUE_WARNING_1:
            tipo_regua = 'Atraso (D+1)'
        elif days_overdue == DAYS_AFTER_DUE_WARNING_2:
            tipo_regua = 'Aviso de Bloqueio (D+10)'
        else:
            tipo_regua = f'Atraso (D+{days_overdue} dias)'
        
        conteudo = (
            f"ATRASO: {cliente.nome}, sua cobrança de R$ {cobranca.valor_total_devido} "
            f"está atrasada em {days_overdue} dias."
        )
        return tipo_regua, conteudo



