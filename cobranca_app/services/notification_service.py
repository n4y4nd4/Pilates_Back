"""
Notification service - Handles notification creation and management.
Following Single Responsibility: only notification-related operations.
"""
from typing import Optional
from django.utils import timezone

from cobranca_app.models import Notificacao, Cobranca
from cobranca_app.core.constants import TipoCanal, StatusEnvio
from cobranca_app.core.utils import log_event
from cobranca_app.core.exceptions import NotificationException


class NotificationService:
    """Service for managing notifications."""
    
    @staticmethod
    def create_notification(
        cobranca: Cobranca,
        tipo_regua: str,
        canal: TipoCanal,
        conteudo: str,
        status: StatusEnvio = StatusEnvio.AGENDADO
    ) -> Notificacao:
        """
        Create a notification record.
        
        Args:
            cobranca: Billing associated with notification
            tipo_regua: Type of payment reminder rule
            canal: Notification channel
            conteudo: Message content
            status: Initial status
        
        Returns:
            Created Notificacao instance
        
        Raises:
            NotificationException: If notification creation fails
        """
        try:
            notification = Notificacao.objects.create(
                cobranca=cobranca,
                tipo_regua=tipo_regua,
                tipo_canal=canal.value,
                conteudo_mensagem=conteudo,
                data_agendada=timezone.now(),
                data_envio_real=timezone.now() if status == StatusEnvio.ENVIADO else None,
                status_envio=status.value
            )
            return notification
        except Exception as e:
            log_event(
                "error",
                "Failed to create notification",
                cobranca_id=cobranca.id if cobranca else None
            )
            raise NotificationException(f"Error creating notification: {e}") from e
    
    @staticmethod
    def get_or_create_placeholder_cobranca(cliente) -> Cobranca:
        """
        Get or create a placeholder billing for notification purposes.
        
        Args:
            cliente: Client instance
        
        Returns:
            Existing or newly created Cobranca instance
        """
        latest = Cobranca.objects.filter(cliente=cliente).order_by("-data_vencimento").first()
        if latest:
            return latest
        
        from decimal import Decimal
        today = timezone.localdate()
        referencia = today.strftime("%Y-%m")
        
        return Cobranca.objects.create(
            cliente=cliente,
            valor_base=Decimal('0.00'),
            valor_multa_juros=Decimal('0.00'),
            valor_total_devido=Decimal('0.00'),
            data_vencimento=today,
            referencia_ciclo=referencia,
            status_cobranca='PENDENTE'
        )



