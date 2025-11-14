# cobranca_app/services/email_service.py
"""
Serviço de envio de e-mail para cobranças.
Mantém assinatura enviar_email_real(cobranca, tipo_regua) -> (bool, str)
Registra logs e retorna tupla (sucesso, detalhe).
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _log_event(level: str, human_msg: str, **meta):
    try:
        getattr(logger, level)(human_msg)
        logger.info({"ts": timezone.now().isoformat(), "msg": human_msg, "meta": meta})
    except Exception:
        logger.exception("Erro ao logar evento de e-mail.")


def enviar_email_real(cobranca, tipo_regua):
    """
    Envia e-mail usando as configurações do settings.py.
    Retorna (True, "mensagem") em caso de sucesso ou (False, "erro...") em caso de falha.
    """
    try:
        contexto = {
            'nome_cliente': cobranca.cliente.nome,
            'valor_total': cobranca.valor_total_devido,
            'data_vencimento': cobranca.data_vencimento.strftime("%d/%m/%Y") if getattr(cobranca, "data_vencimento", None) else "",
            'status_cobranca': "Em Atraso" if getattr(cobranca, "status_cobranca", "") == 'ATRASADO' else "Lembrete",
            'ciclo_referencia': getattr(cobranca, "referencia_ciclo", ""),
        }

        html_message = render_to_string('cobranca_app/email_cobranca.html', contexto)

        send_mail(
            subject=f"Pilates - Aviso de Cobrança: {tipo_regua}",
            message="Use um cliente de e-mail que suporte HTML.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cobranca.cliente.email],
            html_message=html_message,
            fail_silently=False,
        )

        _log_event("info", f"Email enviado para {cobranca.cliente.email}", cobranca_id=getattr(cobranca, "id", None))
        return True, "ENVIADO"

    except Exception as e:
        _log_event("error", f"Erro no envio de e-mail: {e}", cobranca_id=getattr(cobranca, "id", None))
        return False, f"Falha no envio de e-mail: {e}"
