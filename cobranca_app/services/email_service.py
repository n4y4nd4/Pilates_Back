"""
Email notification service.
Following Single Responsibility: only email sending operations.
"""
import logging
from typing import Tuple
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from cobranca_app.models import Cobranca
from cobranca_app.core.constants import StatusCobranca, DATE_FORMAT_DISPLAY
from cobranca_app.core.utils import log_event, format_date_for_display, get_safe_attribute
from cobranca_app.core.exceptions import EmailServiceException, ConfigurationException
from cobranca_app.core.validators import validate_email_config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    @staticmethod
    def send_billing_notification(
        cobranca: Cobranca,
        tipo_regua: str
    ) -> Tuple[bool, str]:
        """
        Send billing notification email.
        
        Args:
            cobranca: Billing instance
            tipo_regua: Type of payment reminder rule
        
        Returns:
            Tuple of (success: bool, detail: str)
        
        Raises:
            EmailServiceException: If email sending fails
            ConfigurationException: If email configuration is invalid
        """
        try:
            validate_email_config()
            
            context = EmailService._build_email_context(cobranca)
            html_message = render_to_string('cobranca_app/email_cobranca.html', context)
            
            subject = f"Pilates - Aviso de Cobrança: {tipo_regua}"
            recipient = cobranca.cliente.email
            
            send_mail(
                subject=subject,
                message="Use um cliente de e-mail que suporte HTML.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=html_message,
                fail_silently=False,
            )
            
            log_event(
                "info",
                f"Email sent successfully to {recipient}",
                cobranca_id=cobranca.id,
                tipo_regua=tipo_regua
            )
            
            return True, "ENVIADO"
            
        except ConfigurationException:
            raise
        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            log_event(
                "error",
                error_msg,
                cobranca_id=get_safe_attribute(cobranca, "id"),
                tipo_regua=tipo_regua
            )
            raise EmailServiceException(error_msg) from e
    
    @staticmethod
    def _build_email_context(cobranca: Cobranca) -> dict:
        """
        Build email template context.
        
        Args:
            cobranca: Billing instance
        
        Returns:
            Dictionary with template context
        """
        status_cobranca = get_safe_attribute(cobranca, "status_cobranca", "")
        is_overdue = status_cobranca == StatusCobranca.ATRASADO.value
        
        return {
            'nome_cliente': cobranca.cliente.nome,
            'valor_total': cobranca.valor_total_devido,
            'data_vencimento': format_date_for_display(cobranca.data_vencimento),
            'status_cobranca': "Em Atraso" if is_overdue else "Lembrete",
            'ciclo_referencia': get_safe_attribute(cobranca, "referencia_ciclo", ""),
        }


# Backward compatibility function
def enviar_email_real(cobranca: Cobranca, tipo_regua: str) -> Tuple[bool, str]:
    """
    Legacy function for backward compatibility.
    
    Args:
        cobranca: Billing instance
        tipo_regua: Type of payment reminder rule
    
    Returns:
        Tuple of (success: bool, detail: str)
    """
    try:
        return EmailService.send_billing_notification(cobranca, tipo_regua)
    except (EmailServiceException, ConfigurationException) as e:
        return False, str(e)
    except Exception as e:
        return False, f"Falha no envio de e-mail: {e}"
