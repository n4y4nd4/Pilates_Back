# cobranca_app/management/commands/startjobs.py

from django.core.management.base import BaseCommand
from django_apscheduler.models import DjangoJobExecution
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from cobranca_app.tasks import rotina_diaria_disparo # IMPORTA SUA FUNÇÃO!
import logging

logger = logging.getLogger(__name__)


def apagar_jobs_antigos():
    # Isso limpa logs antigos para manter o banco de dados leve.
    DjangoJobExecution.objects.delete_old_job_executions(max_age=604_800) # 1 semana


class Command(BaseCommand):
    help = "Inicia o Agendador de Tarefas do Projeto."

    def handle(self, *args, **options):
        # 1. Cria o Agendador
        scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
        
        # 2. Define o Trigger (Quando o job deve rodar)
        # CronTrigger(hour=0, minute=1): Executa todos os dias à 00:01
        trigger = CronTrigger(hour="0", minute="1")

        # 3. Adiciona a Tarefa de Cobrança (sua função)
        scheduler.add_job(
            rotina_diaria_disparo,
            trigger=trigger,
            id="rotina_diaria_cobranca",
            max_instances=1, # Garante que só uma instância rode por vez
            replace_existing=True,
        )
        logger.info("Rotina de cobrança agendada para rodar diariamente às 00:01.")
        
        # 4. Adiciona a Tarefa de Limpeza de Logs (Para rodar semanalmente)
        scheduler.add_job(
            apagar_jobs_antigos,
            trigger=CronTrigger(day_of_week="mon", hour="0", minute="30"), # Segunda-feira, 00:30
            id="limpeza_logs_agendador",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Limpeza de logs agendada para rodar toda segunda-feira.")
        
        
        try:
            logger.info("Iniciando Agendador...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Agendador interrompido manualmente.")
            scheduler.shutdown()
        except Exception as e:
            logger.error(f"Erro ao iniciar o Agendador: {e}")
            scheduler.shutdown()