"""
Scheduled tasks for the billing application.
Following Clean Code: clear separation between task scheduling and business logic.
"""
from cobranca_app.services.cobranca_service import DailyBillingRoutine


def rotina_diaria_disparo_task() -> str:
    """
    Task wrapper for daily billing routine.
    This function is called by the scheduler (django-apscheduler).
    
    Returns:
        Status message from the routine execution
    
    Note:
        In the future, if using Celery, this can be converted to a Celery task.
    """
    return DailyBillingRoutine.execute()
