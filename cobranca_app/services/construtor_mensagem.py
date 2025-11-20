"""
Serviço construtor de mensagem - Cria mensagens de notificação.
Seguindo Single Responsibility: apenas criação de conteúdo de mensagem.
"""
from typing import Tuple
from datetime import date

from cobranca_app.models import Cobranca, Cliente
from cobranca_app.core.constantes import (
    DIAS_ANTES_VENCIMENTO_LEMBRETE,
    DIAS_APOS_VENCIMENTO_AVISO_1,
    DIAS_APOS_VENCIMENTO_AVISO_2
)


class ConstrutorMensagem:
    """Serviço para construir mensagens de notificação."""
    
    @staticmethod
    def construir_mensagem_lembrete(cobranca: Cobranca) -> Tuple[str, str]:
        """
        Constrói mensagem de lembrete (D-3).
        
        Args:
            cobranca: Instância de cobrança
        
        Returns:
            Tupla de (tipo_regua, conteudo_mensagem)
        """
        cliente = cobranca.cliente
        tipo_regua = 'Lembrete (D-3)'
        conteudo = (
            f"Olá {cliente.nome}, sua cobrança de R$ {cobranca.valor_total_devido} "
            f"vencerá em 3 dias ({cobranca.data_vencimento.strftime('%d/%m/%Y')})."
        )
        return tipo_regua, conteudo
    
    @staticmethod
    def construir_mensagem_atraso(cobranca: Cobranca, dias_atraso: int) -> Tuple[str, str]:
        """
        Constrói mensagem de atraso com base nos dias de atraso.
        
        Args:
            cobranca: Instância de cobrança
            dias_atraso: Número de dias de atraso
        
        Returns:
            Tupla de (tipo_regua, conteudo_mensagem)
        """
        cliente = cobranca.cliente
        
        if dias_atraso == DIAS_APOS_VENCIMENTO_AVISO_1:
            tipo_regua = 'Atraso (D+1)'
        elif dias_atraso == DIAS_APOS_VENCIMENTO_AVISO_2:
            tipo_regua = 'Aviso de Bloqueio (D+10)'
        else:
            tipo_regua = f'Atraso (D+{dias_atraso} dias)'
        
        conteudo = (
            f"ATRASO: {cliente.nome}, sua cobrança de R$ {cobranca.valor_total_devido} "
            f"está atrasada em {dias_atraso} dias."
        )
        return tipo_regua, conteudo


