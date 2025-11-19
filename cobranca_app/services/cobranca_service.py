"""
Daily billing routine service.
Orchestrates the daily billing notification process.
Following Clean Code: single responsibility, small functions, clear naming.
"""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from cobranca_app.models import Cobranca
from cobranca_app.core.constants import (
    TipoCanal,
    StatusEnvio,
    DAYS_BEFORE_DUE_REMINDER
)
from cobranca_app.core.utils import log_event
from cobranca_app.services.billing_service import BillingService
from cobranca_app.services.message_builder import MessageBuilder
from cobranca_app.services.email_service import EmailService
from cobranca_app.services.whatsapp_service import WhatsAppService
from cobranca_app.services.notification_service import NotificationService


class DailyBillingRoutine:
    """Service for executing daily billing notification routine."""
    
    @staticmethod
    def execute() -> str:
        """
        Execute the daily billing notification routine.
        
        Returns:
            Status message
        """
        hoje = timezone.localdate()
        log_event("info", f"Starting daily billing routine: {hoje}")
        
        # Step 1: Mark overdue billings
        overdue_count = DailyBillingRoutine._mark_overdue_billings()
        log_event("info", f"Marked {overdue_count} billings as overdue")
        
        # Step 2: Get billings eligible for notifications
        eligible_billings = DailyBillingRoutine._get_eligible_billings(hoje)
        log_event("info", f"Found {len(eligible_billings)} eligible billings for notification")
        
        # Step 3: Process each billing
        for cobranca in eligible_billings:
            DailyBillingRoutine._process_billing_notification(cobranca, hoje)
        
        log_event("info", "Daily billing routine completed")
        return "Disparos e Atualizações Concluídas."
    
    @staticmethod
    def _mark_overdue_billings() -> int:
        """Mark pending billings as overdue."""
        return BillingService.mark_overdue_billings()
    
    @staticmethod
    def _get_eligible_billings(hoje) -> list:
        """
        Get billings eligible for notification.
        
        Args:
            hoje: Current date
        
        Returns:
            List of eligible Cobranca instances
        """
        reminder_date = hoje + timedelta(days=DAYS_BEFORE_DUE_REMINDER)
        
        reminder_billings = BillingService.get_billings_for_reminder(reminder_date)
        overdue_billings = BillingService.get_overdue_billings()
        
        return reminder_billings + overdue_billings
    
    @staticmethod
    def _process_billing_notification(cobranca: Cobranca, hoje) -> None:
        """
        Process notification for a single billing.
        
        Args:
            cobranca: Billing instance
            hoje: Current date
        """
        cliente = cobranca.cliente
        tipo_regua, conteudo = DailyBillingRoutine._build_message(cobranca, hoje)
        
        log_event("info", f"Sending {tipo_regua} to {cliente.nome}")
        
        # Send notifications
        whatsapp_result = DailyBillingRoutine._send_whatsapp_notification(
            cliente, conteudo, tipo_regua
        )
        email_result = DailyBillingRoutine._send_email_notification(
            cobranca, tipo_regua
        )
        
        # Record notifications
        DailyBillingRoutine._record_notifications(
            cobranca=cobranca,
            tipo_regua=tipo_regua,
            conteudo=conteudo,
            whatsapp_success=whatsapp_result[0],
            email_success=email_result[0]
        )
    
    @staticmethod
    def _build_message(cobranca: Cobranca, hoje) -> tuple:
        """
        Build notification message based on billing status.
        
        Args:
            cobranca: Billing instance
            hoje: Current date
        
        Returns:
            Tuple of (tipo_regua, message_content)
        """
        if cobranca.is_atrasado():
            days_overdue = cobranca.calcular_dias_atraso()
            return MessageBuilder.build_overdue_message(cobranca, days_overdue)
        else:
            return MessageBuilder.build_reminder_message(cobranca)
    
    @staticmethod
    def _send_whatsapp_notification(
        cliente,
        conteudo: str,
        tipo_regua: str
    ) -> tuple:
        """
        Send WhatsApp notification if enabled.
        
        Args:
            cliente: Client instance
            conteudo: Message content
            tipo_regua: Type of reminder rule
        
        Returns:
            Tuple of (success: bool, detail: str)
        """
        if not DailyBillingRoutine._is_whatsapp_enabled():
            log_event(
                "info",
                f"WhatsApp disabled for {cliente.nome} (kill switch)",
                cliente_id=cliente.id,
                tipo_regua=tipo_regua
            )
            return False, "Desativado por chave de configuração."
        
        try:
            return WhatsAppService.send_message(cliente, conteudo)
        except Exception as e:
            log_event("error", f"WhatsApp sending failed: {e}", cliente_id=cliente.id)
            return False, str(e)
    
    @staticmethod
    def _send_email_notification(cobranca: Cobranca, tipo_regua: str) -> tuple:
        """
        Send email notification.
        
        Args:
            cobranca: Billing instance
            tipo_regua: Type of reminder rule
        
        Returns:
            Tuple of (success: bool, detail: str)
        """
        try:
            return EmailService.send_billing_notification(cobranca, tipo_regua)
        except Exception as e:
            log_event("error", f"Email sending failed: {e}", cobranca_id=cobranca.id)
            return False, str(e)
    
    @staticmethod
    def _is_whatsapp_enabled() -> bool:
        """Check if WhatsApp notifications are enabled."""
        meta_cfg = getattr(settings, "META_API_SETTINGS", {})
        return meta_cfg.get("WHATSAPP_ENABLED", True)
    
    @staticmethod
    def _record_notifications(
        cobranca: Cobranca,
        tipo_regua: str,
        conteudo: str,
        whatsapp_success: bool,
        email_success: bool
    ) -> None:
        """
        Record notification attempts in database.
        
        Args:
            cobranca: Billing instance
            tipo_regua: Type of reminder rule
            conteudo: Message content
            whatsapp_success: WhatsApp sending result
            email_success: Email sending result
        """
        # Ensure we have a billing for notification
        billing_for_notification = cobranca or NotificationService.get_or_create_placeholder_cobranca(
            cobranca.cliente
        )
        
        # Record WhatsApp notification
        whatsapp_status = StatusEnvio.ENVIADO if whatsapp_success else StatusEnvio.FALHA
        NotificationService.create_notification(
            cobranca=billing_for_notification,
            tipo_regua=tipo_regua,
            canal=TipoCanal.WHATSAPP,
            conteudo=conteudo,
            status=whatsapp_status
        )
        
        # Record Email notification
        email_status = StatusEnvio.ENVIADO if email_success else StatusEnvio.FALHA
        NotificationService.create_notification(
            cobranca=billing_for_notification,
            tipo_regua=tipo_regua,
            canal=TipoCanal.EMAIL,
            conteudo=conteudo,
            status=email_status
        )


# Backward compatibility function
def rotina_diaria_disparo() -> str:
    """
    Legacy function for backward compatibility.
    
    Returns:
        Status message
    """
    return DailyBillingRoutine.execute()
