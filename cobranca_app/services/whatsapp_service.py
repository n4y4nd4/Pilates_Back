# cobranca_app/services/whatsapp_service.py
"""
Serviço de envio WhatsApp (Meta Cloud API) — texto simples.
- Mantém a assinatura enviar_whatsapp_real(cliente, mensagem)
- Registra Notificacao usando os campos existentes no seu model
- Logs híbridos (legível + JSON)
"""

import time
import json
import logging
from typing import Tuple, Optional

import requests
from django.conf import settings
from django.utils import timezone

from cobranca_app.models import Notificacao, Cobranca

logger = logging.getLogger(__name__)


def _log_event(level: str, human_msg: str, **meta):
    """
    Log híbrido: mensagem legível + JSON com metadados.
    level: 'info', 'warning', 'error', ...
    """
    # Legível
    getattr(logger, level)(human_msg)

    # Estruturado (JSON) — bom para envio a observability/ELK se configurado
    try:
        meta_record = {
            "ts": timezone.now().isoformat(),
            "msg": human_msg,
            "meta": meta
        }
        getattr(logger, level)(json.dumps(meta_record, default=str))
    except Exception:
        # Não falhar por causa do log
        logger.exception("Erro ao gerar log JSON.")


def _normaliza_telefone(raw_number: Optional[str]) -> str:
    """
    Normaliza telefone para apenas dígitos (DDI + DDD + número).
    Ex.: "+55 (21) 9 8765-4321" -> "5521987654321"
    """
    if not raw_number:
        return ""
    digits = "".join(ch for ch in str(raw_number) if ch.isdigit())
    return digits


def _encontra_ultima_cobranca(cliente):
    """
    Busca a cobrança mais recente (por data_vencimento) para associar à Notificação.
    Retorna None se não encontrar.
    """
    try:
        return Cobranca.objects.filter(cliente=cliente).order_by("-data_vencimento").first()
    except Exception:
        return None


def _criar_notificacao_db(cobranca_obj, tipo_regua, conteudo_mensagem, status_envio):
    """
    Cria um registro no model Notificacao usando os campos que seu model possui.
    Campos usados: cobranca, tipo_regua, tipo_canal, conteudo_mensagem, data_agendada, data_envio_real, status_envio
    """
    try:
        Notificacao.objects.create(
            cobranca=cobranca_obj,
            tipo_regua=(tipo_regua or ""),
            tipo_canal="WhatsApp",
            conteudo_mensagem=conteudo_mensagem,
            data_agendada=timezone.now(),
            data_envio_real=timezone.now(),
            status_envio=status_envio
        )
    except Exception as e:
        # Não interromper o fluxo por erro de escrita no BD; apenas logamos
        _log_event("error", "Erro ao criar Notificacao no banco", exception=str(e))


def enviar_whatsapp_real(cliente, mensagem: str, max_retries: int = 3, backoff_factor: float = 1.0) -> Tuple[bool, str]:
    """
    Envia mensagem via WhatsApp Cloud API (texto simples).
    Mantém compatibilidade com sua assinatura atual.

    Retorna:
        (True, "ENVIADO")  em caso de sucesso
        (False, "mensagem de erro...") em caso de falha
    """
    # 1) Obter configuração do settings
    meta_cfg = getattr(settings, "META_API_SETTINGS", None)
    if not meta_cfg:
        _log_event("error", "META_API_SETTINGS ausente em settings.py")
        return False, "Configuração META_API_SETTINGS não encontrada."

    token = meta_cfg.get("TOKEN")
    phone_id = meta_cfg.get("PHONE_ID")
    url_base = meta_cfg.get("URL_BASE")

    if not token or not phone_id or not url_base or len(str(token)) < 30:
        _log_event("error", "Credenciais Meta inválidas", token_present=bool(token), phone_id=phone_id)
        return False, "Falha de Autenticação: Token/PHONE_ID/URL_BASE inválidos."

    # 2) Normaliza número do cliente
    numero_raw = getattr(cliente, "telefone_whatsapp", None)
    numero = _normaliza_telefone(numero_raw)
    if not numero:
        _log_event("warning", "Número inválido ou ausente no cliente", cliente_id=getattr(cliente, "id", None))
        return False, "Número de telefone inválido ou ausente no cliente."

    # 3) Encontra cobrança associada (opcional) para referenciar na Notificação
    cobranca_obj = _encontra_ultima_cobranca(cliente)

    # 4) Monta URL e payload (texto simples)
    # Garante que URL_BASE termina com '/'
    base = url_base if str(url_base).endswith('/') else f"{url_base}/"
    url = f"{base}{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensagem}
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    _log_event("info", f"[SEND] Tentando enviar WhatsApp para {numero}", cliente_id=getattr(cliente, "id", None))

    # 5) Retry com backoff exponencial simples
    attempt = 0
    last_error = None
    while attempt < max_retries:
        attempt += 1
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            status = getattr(resp, "status_code", None)
            text = getattr(resp, "text", "")

            _log_event("info", f"[HTTP] status={status} resp={text[:200]}", attempt=attempt, phone=numero)

            if status in (200, 201):
                # sucesso
                _criar_notificacao_db(cobranca_obj, tipo_regua=None, conteudo_mensagem=mensagem, status_envio="ENVIADO")
                _log_event("info", f"[OK] Mensagem enviada para {numero}", cliente_id=getattr(cliente, "id", None))
                return True, "ENVIADO"
            else:
                last_error = f"Falha WhatsApp (Status: {status}, Erro: {text})"
                _log_event("warning", last_error, attempt=attempt, phone=numero)
                # se vamos tentar de novo, espera
                if attempt < max_retries:
                    time.sleep(backoff_factor * (2 ** (attempt - 1)))
                    continue
                # ultima tentativa falhou: registra e retorna
                _criar_notificacao_db(cobranca_obj, tipo_regua=None, conteudo_mensagem=mensagem, status_envio="FALHA")
                return False, last_error

        except requests.exceptions.RequestException as e:
            last_error = f"Falha de conexão (Tentativa {attempt}): {e}"
            _log_event("error", last_error, attempt=attempt, phone=numero)
            if attempt < max_retries:
                time.sleep(backoff_factor * (2 ** (attempt - 1)))
                continue
            _criar_notificacao_db(cobranca_obj, tipo_regua=None, conteudo_mensagem=mensagem, status_envio="FALHA")
            return False, last_error

    # fallback
    _criar_notificacao_db(cobranca_obj, tipo_regua=None, conteudo_mensagem=mensagem, status_envio="FALHA")
    return False, last_error or "Falha desconhecida no envio WhatsApp."
