"""
Management command to start the task scheduler.
Following Clean Code: clear separation of concerns and configuration.
"""
from django.core.management.base import BaseCommand
from django_apscheduler.models import DjangoJobExecution
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import logging

from cobranca_app.tasks import rotina_diaria_disparo_task

logger = logging.getLogger(__name__)


# Constants for job configuration
DAILY_BILLING_JOB_HOUR = "0"
DAILY_BILLING_JOB_MINUTE = "1"
CLEANUP_JOB_DAY = "mon"
CLEANUP_JOB_HOUR = "0"
CLEANUP_JOB_MINUTE = "30"
CLEANUP_MAX_AGE_SECONDS = 604_800  # 1 week


def cleanup_old_job_executions() -> None:
    """
    Clean up old job execution logs to keep database lightweight.
    
    This function is scheduled to run weekly.
    """
    DjangoJobExecution.objects.delete_old_job_executions(
        max_age=CLEANUP_MAX_AGE_SECONDS
    )


class Command(BaseCommand):
    """Command to start the task scheduler."""
    
    help = "Inicia o Agendador de Tarefas do Projeto."
    
    def handle(self, *args, **options) -> None:
        """Start the scheduler with configured jobs."""
        scheduler = self._create_scheduler()
        self._schedule_daily_billing_job(scheduler)
        self._schedule_cleanup_job(scheduler)
        self._start_scheduler(scheduler)
    
    def _create_scheduler(self) -> BackgroundScheduler:
        """Create and configure the scheduler."""
        return BackgroundScheduler(timezone=settings.TIME_ZONE)
    
    def _schedule_daily_billing_job(self, scheduler: BackgroundScheduler) -> None:
        """Schedule the daily billing routine job."""
        trigger = CronTrigger(
            hour=DAILY_BILLING_JOB_HOUR,
            minute=DAILY_BILLING_JOB_MINUTE
        )
        
        scheduler.add_job(
            rotina_diaria_disparo_task,
            trigger=trigger,
            id="rotina_diaria_cobranca",
            max_instances=1,
            replace_existing=True,
        )
        
        logger.info("Rotina de cobrança agendada para rodar diariamente às 00:01.")
    
    def _schedule_cleanup_job(self, scheduler: BackgroundScheduler) -> None:
        """Schedule the cleanup job for old logs."""
        trigger = CronTrigger(
            day_of_week=CLEANUP_JOB_DAY,
            hour=CLEANUP_JOB_HOUR,
            minute=CLEANUP_JOB_MINUTE
        )
        
        scheduler.add_job(
            cleanup_old_job_executions,
            trigger=trigger,
            id="limpeza_logs_agendador",
            max_instances=1,
            replace_existing=True,
        )
        
        logger.info("Limpeza de logs agendada para rodar toda segunda-feira.")
    
    def _start_scheduler(self, scheduler: BackgroundScheduler) -> None:
        """Start the scheduler with error handling."""
        try:
            logger.info("Iniciando Agendador...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Agendador interrompido manualmente.")
            scheduler.shutdown()
        except Exception as e:
            logger.error(f"Erro ao iniciar o Agendador: {e}")
            scheduler.shutdown()
