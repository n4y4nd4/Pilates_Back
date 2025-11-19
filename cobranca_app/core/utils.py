"""
Shared utility functions.
Following DRY principle: reusable functions used across the application.
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from datetime import date, timedelta

logger = logging.getLogger(__name__)


def calculate_due_date(
    start_date: date,
    periodicity_months: int,
    days_per_month: int = 30
) -> date:
    """
    Calculate the due date based on start date and periodicity.
    
    Args:
        start_date: Contract start date
        periodicity_months: Number of months in the billing period
        days_per_month: Days to consider per month (default: 30)
    
    Returns:
        Calculated due date
    """
    calculated_date = start_date + timedelta(days=periodicity_months * days_per_month)
    today = timezone.localdate()
    
    # If calculated date is in the past, calculate from today
    if calculated_date < today:
        return today + timedelta(days=periodicity_months * days_per_month)
    
    return calculated_date


def format_date_for_display(date_value: Optional[date]) -> str:
    """
    Format a date for display purposes.
    
    Args:
        date_value: Date to format
    
    Returns:
        Formatted date string or empty string if None
    """
    if not date_value:
        return ""
    return date_value.strftime("%d/%m/%Y")


def log_event(
    level: str,
    message: str,
    logger_instance: Optional[logging.Logger] = None,
    **metadata: Any
) -> None:
    """
    Log an event with structured metadata.
    
    Args:
        level: Log level (info, warning, error, etc.)
        message: Human-readable message
        logger_instance: Logger instance (defaults to module logger)
        **metadata: Additional metadata to log
    """
    log = logger_instance or logger
    
    try:
        # Log readable message
        getattr(log, level)(message)
        
        # Log structured metadata
        structured_data = {
            "timestamp": timezone.now().isoformat(),
            "message": message,
            "metadata": metadata
        }
        log.info(f"STRUCTURED_LOG: {structured_data}")
    except Exception as e:
        log.exception(f"Error logging event: {e}")


def normalize_phone_number(phone_number: Optional[str]) -> str:
    """
    Normalize phone number to digits only.
    
    Args:
        phone_number: Raw phone number string
    
    Returns:
        Normalized phone number (digits only)
    
    Example:
        "+55 (21) 9 8765-4321" -> "5521987654321"
    """
    if not phone_number:
        return ""
    return "".join(char for char in str(phone_number) if char.isdigit())


def get_safe_attribute(obj: Any, attribute: str, default: Any = None) -> Any:
    """
    Safely get an attribute from an object.
    
    Args:
        obj: Object to get attribute from
        attribute: Attribute name
        default: Default value if attribute doesn't exist
    
    Returns:
        Attribute value or default
    """
    return getattr(obj, attribute, default)



