"""
Validation functions for business rules.
Following Single Responsibility: each validator has one clear purpose.
"""
from typing import Optional
from cobranca_app.core.exceptions import InvalidDataException, ConfigurationException
from cobranca_app.core.constants import MIN_TOKEN_LENGTH


def validate_phone_number(phone_number: Optional[str]) -> None:
    """
    Validate phone number format.
    
    Args:
        phone_number: Phone number to validate
    
    Raises:
        InvalidDataException: If phone number is invalid
    """
    if not phone_number:
        raise InvalidDataException("Phone number is required")
    
    digits_only = "".join(char for char in str(phone_number) if char.isdigit())
    if len(digits_only) < 10:
        raise InvalidDataException("Phone number must have at least 10 digits")


def validate_whatsapp_config(config: dict) -> None:
    """
    Validate WhatsApp API configuration.
    
    Args:
        config: Configuration dictionary
    
    Raises:
        ConfigurationException: If configuration is invalid
    """
    if not config:
        raise ConfigurationException("META_API_SETTINGS configuration not found")
    
    token = config.get("TOKEN")
    phone_id = config.get("PHONE_ID")
    url_base = config.get("URL_BASE")
    
    if not token or not phone_id or not url_base:
        raise ConfigurationException("Missing required WhatsApp configuration: TOKEN, PHONE_ID, or URL_BASE")
    
    if len(str(token)) < MIN_TOKEN_LENGTH:
        raise ConfigurationException(f"Token must be at least {MIN_TOKEN_LENGTH} characters long")


def validate_email_config() -> None:
    """
    Validate email configuration.
    
    Raises:
        ConfigurationException: If email configuration is invalid
    """
    from django.conf import settings
    
    required_settings = [
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL'
    ]
    
    missing = [setting for setting in required_settings if not getattr(settings, setting, None)]
    
    if missing:
        raise ConfigurationException(f"Missing email configuration: {', '.join(missing)}")



