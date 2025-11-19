"""
Constants used throughout the application.
Following Clean Code principles: no magic numbers or strings.
"""
from enum import Enum
from datetime import timedelta


class StatusCliente(str, Enum):
    """Client status options."""
    ATIVO = 'ATIVO'
    INATIVO_ATRASO = 'INATIVO_ATRASO'
    INATIVO_MANUAL = 'INATIVO_MANUAL'


class StatusCobranca(str, Enum):
    """Billing status options."""
    PENDENTE = 'PENDENTE'
    PAGO = 'PAGO'
    ATRASADO = 'ATRASADO'
    CANCELADO = 'CANCELADO'


class StatusEnvio(str, Enum):
    """Notification sending status options."""
    AGENDADO = 'AGENDADO'
    ENVIADO = 'ENVIADO'
    FALHA = 'FALHA'


class TipoCanal(str, Enum):
    """Notification channel types."""
    EMAIL = 'Email'
    WHATSAPP = 'WhatsApp'


class TipoRegua(str, Enum):
    """Payment reminder rule types."""
    LEMBRETE_D3 = 'Lembrete (D-3)'
    ATRASO_D1 = 'Atraso (D+1)'
    AVISO_BLOQUEIO_D10 = 'Aviso de Bloqueio (D+10)'


# Business Rules Constants
DAYS_PER_MONTH = 30
DAYS_BEFORE_DUE_REMINDER = 3
DAYS_AFTER_DUE_WARNING_1 = 1
DAYS_AFTER_DUE_WARNING_2 = 10

# WhatsApp API Constants
MIN_TOKEN_LENGTH = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
REQUEST_TIMEOUT_SECONDS = 12

# Date Format Constants
DATE_FORMAT_DISPLAY = "%d/%m/%Y"
DATE_FORMAT_REFERENCE = "%Y-%m"

# HTTP Status Codes
HTTP_SUCCESS_CODES = (200, 201)



