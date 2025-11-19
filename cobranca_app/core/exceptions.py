"""
Custom exceptions for the billing application.
Following Clean Code: specific exceptions for better error handling.
"""


class BillingException(Exception):
    """Base exception for billing-related errors."""
    pass


class ClienteException(BillingException):
    """Exception related to client operations."""
    pass


class CobrancaException(BillingException):
    """Exception related to billing operations."""
    pass


class NotificationException(BillingException):
    """Exception related to notification operations."""
    pass


class EmailServiceException(NotificationException):
    """Exception related to email sending."""
    pass


class WhatsAppServiceException(NotificationException):
    """Exception related to WhatsApp sending."""
    pass


class ConfigurationException(BillingException):
    """Exception related to configuration errors."""
    pass


class InvalidDataException(BillingException):
    """Exception for invalid data validation."""
    pass



