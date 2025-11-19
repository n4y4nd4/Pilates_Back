"""
Client service - Handles client business logic.
Following Single Responsibility: only client-related operations.
"""
from cobranca_app.models import Cliente
from cobranca_app.services.billing_service import BillingService
from cobranca_app.core.exceptions import ClienteException
from cobranca_app.core.utils import log_event


class ClienteService:
    """Service for managing clients."""
    
    @staticmethod
    def create_client_with_initial_billing(cliente: Cliente) -> None:
        """
        Create a client and generate their first billing.
        
        Args:
            cliente: Client instance to save
        
        Raises:
            ClienteException: If client creation fails
        """
        try:
            cliente.save()
            
            if cliente.plano:
                BillingService.create_initial_billing(cliente)
                log_event("info", f"Client created with initial billing", cliente_id=cliente.id)
            else:
                log_event("warning", f"Client created without plan", cliente_id=cliente.id)
                
        except Exception as e:
            log_event("error", f"Failed to create client", cliente_id=getattr(cliente, "id", None))
            raise ClienteException(f"Error creating client: {e}") from e



