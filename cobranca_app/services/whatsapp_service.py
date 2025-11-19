"""
WhatsApp notification service.
Following Single Responsibility: only WhatsApp sending operations.
"""
import time
import logging
from typing import Tuple, Optional
import requests
from django.conf import settings
from django.utils import timezone

from cobranca_app.models import Cliente, Cobranca, Notificacao
from cobranca_app.core.constants import (
    TipoCanal,
    StatusEnvio,
    MIN_TOKEN_LENGTH,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BACKOFF_FACTOR,
    REQUEST_TIMEOUT_SECONDS,
    HTTP_SUCCESS_CODES
)
from cobranca_app.core.utils import (
    log_event,
    normalize_phone_number,
    get_safe_attribute
)
from cobranca_app.core.exceptions import (
    WhatsAppServiceException,
    ConfigurationException,
    InvalidDataException
)
from cobranca_app.core.validators import (
    validate_whatsapp_config,
    validate_phone_number
)
from cobranca_app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp notifications."""
    
    @staticmethod
    def send_message(
        cliente: Cliente,
        mensagem: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    ) -> Tuple[bool, str]:
        """
        Send WhatsApp message to client.
        
        Args:
            cliente: Client instance
            mensagem: Message content
            max_retries: Maximum retry attempts
            backoff_factor: Backoff multiplier for retries
        
        Returns:
            Tuple of (success: bool, detail: str)
        
        Raises:
            WhatsAppServiceException: If sending fails
            ConfigurationException: If configuration is invalid
            InvalidDataException: If phone number is invalid
        """
        try:
            config = WhatsAppService._get_config()
            validate_whatsapp_config(config)
            
            phone_number = WhatsAppService._validate_and_normalize_phone(cliente)
            cobranca = WhatsAppService._find_associated_billing(cliente)
            
            url = WhatsAppService._build_api_url(config)
            payload = WhatsAppService._build_payload(phone_number, mensagem)
            headers = WhatsAppService._build_headers(config)
            
            return WhatsAppService._send_with_retry(
                url=url,
                headers=headers,
                payload=payload,
                phone_number=phone_number,
                mensagem=mensagem,
                cobranca=cobranca,
                max_retries=max_retries,
                backoff_factor=backoff_factor
            )
            
        except (ConfigurationException, InvalidDataException):
            raise
        except Exception as e:
            error_msg = f"Unexpected error sending WhatsApp: {e}"
            log_event("error", error_msg, cliente_id=get_safe_attribute(cliente, "id"))
            raise WhatsAppServiceException(error_msg) from e
    
    @staticmethod
    def _get_config() -> dict:
        """Get WhatsApp API configuration from settings."""
        config = getattr(settings, "META_API_SETTINGS", None)
        if not config:
            raise ConfigurationException("META_API_SETTINGS not found in settings")
        return config
    
    @staticmethod
    def _validate_and_normalize_phone(cliente: Cliente) -> str:
        """Validate and normalize client phone number."""
        phone_raw = get_safe_attribute(cliente, "telefone_whatsapp")
        phone_normalized = normalize_phone_number(phone_raw)
        
        if not phone_normalized:
            raise InvalidDataException("Invalid or missing phone number")
        
        return phone_normalized
    
    @staticmethod
    def _find_associated_billing(cliente: Cliente) -> Optional[Cobranca]:
        """Find the most recent billing for the client."""
        try:
            return Cobranca.objects.filter(cliente=cliente).order_by("-data_vencimento").first()
        except Exception:
            return None
    
    @staticmethod
    def _build_api_url(config: dict) -> str:
        """Build WhatsApp API URL."""
        url_base = config.get("URL_BASE", "")
        phone_id = config.get("PHONE_ID", "")
        
        base = url_base if str(url_base).endswith('/') else f"{url_base}/"
        return f"{base}{phone_id}/messages"
    
    @staticmethod
    def _build_payload(phone_number: str, mensagem: str) -> dict:
        """Build WhatsApp API payload."""
        return {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": mensagem}
        }
    
    @staticmethod
    def _build_headers(config: dict) -> dict:
        """Build HTTP headers for WhatsApp API."""
        token = config.get("TOKEN", "")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _send_with_retry(
        url: str,
        headers: dict,
        payload: dict,
        phone_number: str,
        mensagem: str,
        cobranca: Optional[Cobranca],
        max_retries: int,
        backoff_factor: float
    ) -> Tuple[bool, str]:
        """Send message with retry logic."""
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            attempt += 1
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS
                )
                
                if response.status_code in HTTP_SUCCESS_CODES:
                    WhatsAppService._record_success(cobranca, mensagem)
                    log_event(
                        "info",
                        f"WhatsApp message sent successfully to {phone_number}",
                        cliente_id=get_safe_attribute(cobranca, "cliente.id") if cobranca else None
                    )
                    return True, "ENVIADO"
                else:
                    last_error = f"WhatsApp API error (Status: {response.status_code}, Response: {response.text[:200]})"
                    log_event("warning", last_error, attempt=attempt, phone=phone_number)
                    
            except requests.exceptions.RequestException as e:
                last_error = f"Connection error (Attempt {attempt}): {e}"
                log_event("error", last_error, attempt=attempt, phone=phone_number)
            
            # Wait before retry if not last attempt
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** (attempt - 1))
                time.sleep(wait_time)
        
        # All retries failed
        WhatsAppService._record_failure(cobranca, mensagem, last_error)
        return False, last_error or "Unknown WhatsApp sending error"
    
    @staticmethod
    def _record_success(cobranca: Optional[Cobranca], mensagem: str) -> None:
        """Record successful notification."""
        if cobranca:
            NotificationService.create_notification(
                cobranca=cobranca,
                tipo_regua="",
                canal=TipoCanal.WHATSAPP,
                conteudo=mensagem,
                status=StatusEnvio.ENVIADO
            )
    
    @staticmethod
    def _record_failure(
        cobranca: Optional[Cobranca],
        mensagem: str,
        error: Optional[str]
    ) -> None:
        """Record failed notification."""
        if cobranca:
            NotificationService.create_notification(
                cobranca=cobranca,
                tipo_regua="",
                canal=TipoCanal.WHATSAPP,
                conteudo=mensagem,
                status=StatusEnvio.FALHA
            )


# Backward compatibility function
def enviar_whatsapp_real(
    cliente: Cliente,
    mensagem: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
) -> Tuple[bool, str]:
    """
    Legacy function for backward compatibility.
    
    Args:
        cliente: Client instance
        mensagem: Message content
        max_retries: Maximum retry attempts
        backoff_factor: Backoff multiplier
    
    Returns:
        Tuple of (success: bool, detail: str)
    """
    try:
        return WhatsAppService.send_message(cliente, mensagem, max_retries, backoff_factor)
    except (WhatsAppServiceException, ConfigurationException, InvalidDataException) as e:
        return False, str(e)
    except Exception as e:
        return False, f"Falha no envio WhatsApp: {e}"
