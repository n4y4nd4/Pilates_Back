"""
Billing service - Handles billing creation and business logic.
Following Single Responsibility: only billing-related operations.
"""
from typing import Optional
from decimal import Decimal
from django.utils import timezone
from datetime import date, timedelta

from cobranca_app.models import Cliente, Cobranca, Plano
from cobranca_app.core.constants import (
    StatusCobranca,
    DATE_FORMAT_REFERENCE,
    DAYS_PER_MONTH,
    DAYS_BEFORE_DUE_REMINDER,
    DAYS_AFTER_DUE_WARNING_1,
    DAYS_AFTER_DUE_WARNING_2
)
from cobranca_app.core.utils import calculate_due_date, log_event
from cobranca_app.core.exceptions import CobrancaException


class BillingService:
    """Service for managing billings."""
    
    @staticmethod
    def create_initial_billing(cliente: Cliente) -> Cobranca:
        """
        Create the first billing for a new client.
        
        Args:
            cliente: Client instance
        
        Returns:
            Created Cobranca instance
        
        Raises:
            CobrancaException: If billing creation fails
        """
        if not cliente.plano:
            raise CobrancaException("Client must have a plan to create billing")
        
        try:
            due_date = cliente.calcular_proxima_data_vencimento()
            valor_base = cliente.plano.valor_base
            
            return Cobranca.objects.create(
                cliente=cliente,
                valor_base=valor_base,
                valor_multa_juros=Decimal('0.00'),
                valor_total_devido=valor_base,
                data_vencimento=due_date,
                referencia_ciclo=due_date.strftime(DATE_FORMAT_REFERENCE),
                status_cobranca=StatusCobranca.PENDENTE.value
            )
        except Exception as e:
            log_event("error", "Failed to create initial billing", cliente_id=cliente.id)
            raise CobrancaException(f"Error creating billing: {e}") from e
    
    @staticmethod
    def mark_overdue_billings() -> int:
        """
        Mark pending billings as overdue if past due date.
        
        Returns:
            Number of billings marked as overdue
        """
        hoje = timezone.localdate()
        overdue_billings = Cobranca.objects.filter(
            status_cobranca=StatusCobranca.PENDENTE.value,
            data_vencimento__lt=hoje
        )
        
        count = overdue_billings.count()
        for billing in overdue_billings:
            billing.marcar_como_atrasado()
        
        return count
    
    @staticmethod
    def get_billings_for_reminder(reminder_date: date) -> list:
        """
        Get billings that need reminder notification.
        
        Args:
            reminder_date: Date to check for reminders
        
        Returns:
            List of Cobranca instances
        """
        return list(
            Cobranca.objects.filter(
                status_cobranca=StatusCobranca.PENDENTE.value,
                data_vencimento=reminder_date
            ).select_related('cliente')
        )
    
    @staticmethod
    def get_overdue_billings() -> list:
        """
        Get all overdue billings.
        
        Returns:
            List of overdue Cobranca instances
        """
        return list(
            Cobranca.objects.filter(
                status_cobranca=StatusCobranca.ATRASADO.value
            ).select_related('cliente')
        )



