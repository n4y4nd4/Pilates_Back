"""
Serviço de notificação - Gerencia criação e gerenciamento de notificações.
Seguindo Single Responsibility: apenas operações relacionadas a notificação.
"""
from typing import Optional
from django.utils import timezone

from cobranca_app.models import Notificacao, Cobranca
from cobranca_app.core.constantes import TipoCanal, StatusEnvio
from cobranca_app.core.utilitarios import registrar_evento
from cobranca_app.core.excecoes import ExcecaoNotificacao


class ServicoNotificacao:
    """Serviço para gerenciar notificações."""
    
    @staticmethod
    def criar_notificacao(
        cobranca: Cobranca,
        tipo_regua: str,
        canal: TipoCanal,
        conteudo: str,
        status: StatusEnvio = StatusEnvio.AGENDADO
    ) -> Notificacao:
        """
        Cria um registro de notificação.
        
        Args:
            cobranca: Cobrança associada à notificação
            tipo_regua: Tipo de regra de lembrete de pagamento
            canal: Canal de notificação
            conteudo: Conteúdo da mensagem
            status: Status inicial
        
        Returns:
            Instância de Notificacao criada
        
        Raises:
            ExcecaoNotificacao: Se a criação da notificação falhar
        """
        try:
            notificacao = Notificacao.objects.create(
                cobranca=cobranca,
                tipo_regua=tipo_regua,
                tipo_canal=canal.value,
                conteudo_mensagem=conteudo,
                data_agendada=timezone.now(),
                data_envio_real=timezone.now() if status == StatusEnvio.ENVIADO else None,
                status_envio=status.value
            )
            return notificacao
        except Exception as e:
            registrar_evento(
                "error",
                "Falha ao criar notificação",
                cobranca_id=cobranca.id if cobranca else None
            )
            raise ExcecaoNotificacao(f"Erro ao criar notificação: {e}") from e
    
    @staticmethod
    def obter_ou_criar_cobranca_placeholder(cliente) -> Cobranca:
        """
        Obtém ou cria uma cobrança placeholder para fins de notificação.
        
        Args:
            cliente: Instância do cliente
        
        Returns:
            Instância de Cobranca existente ou recém-criada
        """
        mais_recente = Cobranca.objects.filter(cliente=cliente).order_by("-data_vencimento").first()
        if mais_recente:
            return mais_recente
        
        from decimal import Decimal
        hoje = timezone.localdate()
        referencia = hoje.strftime("%Y-%m")
        
        return Cobranca.objects.create(
            cliente=cliente,
            valor_base=Decimal('0.00'),
            valor_multa_juros=Decimal('0.00'),
            valor_total_devido=Decimal('0.00'),
            data_vencimento=hoje,
            referencia_ciclo=referencia,
            status_cobranca='PENDENTE'
        )


