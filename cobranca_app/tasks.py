# cobranca_app/tasks.py
"""
Tasks orquestradoras (sem Celery por enquanto).
Mantém a função rotina_diaria_disparo() sendo chamada a partir daqui para compatibilidade.
"""

from cobranca_app.services.cobranca_service import rotina_diaria_disparo

def rotina_diaria_disparo_task():
    """
    Wrapper simples para compatibilidade com o que você já chama.
    No futuro, se usar Celery, transforme esse wrapper em task do Celery.
    """
    return rotina_diaria_disparo()
