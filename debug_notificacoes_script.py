import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pilates_cobranca.settings')
django.setup()

from cobranca_app.models import Notificacao, Cobranca
from cobranca_app.core.constantes import StatusEnvio

print("--- Debugging Notifications ---")
total_notificacoes = Notificacao.objects.count()
print(f"Total Notificacoes: {total_notificacoes}")

statuses = [status.value for status in StatusEnvio]
for status in statuses:
    count = Notificacao.objects.filter(status_envio=status).count()
    print(f"Status '{status}': {count}")

print("\n--- Last 5 Notifications ---")
last_5 = Notificacao.objects.order_by('-data_agendada')[:5]
for n in last_5:
    print(f"ID: {n.id}, Canal: {n.tipo_canal}, Status: {n.status_envio}, Data: {n.data_agendada}, Cliente: {n.cobranca.cliente.nome}")

print("\n--- Checking for Email Notifications specifically ---")
email_count = Notificacao.objects.filter(tipo_canal__icontains='email').count()
print(f"Total Email Notifications: {email_count}")

sent_email_count = Notificacao.objects.filter(tipo_canal__icontains='email', status_envio='ENVIADO').count()
print(f"Sent Email Notifications: {sent_email_count}")
