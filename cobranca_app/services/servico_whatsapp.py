"""
Serviço de notificação por WhatsApp.
Seguindo Single Responsibility: apenas operações de envio de WhatsApp.
"""
import time
import logging
from typing import Tuple, Optional
import requests
from django.conf import settings
from django.utils import timezone

from cobranca_app.models import Cliente, Cobranca, Notificacao
from cobranca_app.core.constantes import (
    TipoCanal,
    StatusEnvio,
    TAMANHO_MIN_TOKEN,
    TENTATIVAS_MAX_PADRAO,
    FATOR_BACKOFF_PADRAO,
    TIMEOUT_REQUISICAO_SEGUNDOS,
    CODIGOS_HTTP_SUCESSO
)
from cobranca_app.core.utilitarios import (
    registrar_evento,
    normalizar_numero_telefone,
    obter_atributo_seguro
)
from cobranca_app.core.excecoes import (
    ExcecaoServicoWhatsApp,
    ExcecaoConfiguracao,
    ExcecaoDadosInvalidos
)
from cobranca_app.core.validadores import (
    validar_config_whatsapp,
    validar_numero_telefone
)
from cobranca_app.services.servico_notificacao import ServicoNotificacao

logger = logging.getLogger(__name__)


class ServicoWhatsApp:
    """Serviço para enviar notificações por WhatsApp."""
    
    @staticmethod
    def enviar_mensagem(
        cliente: Cliente,
        mensagem: str,
        tentativas_max: int = TENTATIVAS_MAX_PADRAO,
        fator_backoff: float = FATOR_BACKOFF_PADRAO
    ) -> Tuple[bool, str]:
        """
        Envia mensagem WhatsApp para o cliente.
        
        Args:
            cliente: Instância do cliente
            mensagem: Conteúdo da mensagem
            tentativas_max: Número máximo de tentativas
            fator_backoff: Multiplicador de backoff para tentativas
        
        Returns:
            Tupla de (sucesso: bool, detalhe: str)
        
        Raises:
            ExcecaoServicoWhatsApp: Se o envio falhar
            ExcecaoConfiguracao: Se a configuração for inválida
            ExcecaoDadosInvalidos: Se o número de telefone for inválido
        """
        try:
            config = ServicoWhatsApp._obter_config()
            validar_config_whatsapp(config)
            
            numero_telefone = ServicoWhatsApp._validar_e_normalizar_telefone(cliente)
            cobranca = ServicoWhatsApp._encontrar_cobranca_associada(cliente)
            
            url = ServicoWhatsApp._construir_url_api(config)
            payload = ServicoWhatsApp._construir_payload(numero_telefone, mensagem)
            headers = ServicoWhatsApp._construir_headers(config)
            
            return ServicoWhatsApp._enviar_com_tentativas(
                url=url,
                headers=headers,
                payload=payload,
                numero_telefone=numero_telefone,
                mensagem=mensagem,
                cobranca=cobranca,
                tentativas_max=tentativas_max,
                fator_backoff=fator_backoff
            )
            
        except (ExcecaoConfiguracao, ExcecaoDadosInvalidos):
            raise
        except Exception as e:
            mensagem_erro = f"Erro inesperado ao enviar WhatsApp: {e}"
            registrar_evento("error", mensagem_erro, cliente_cpf=obter_atributo_seguro(cliente, "cpf"))
            raise ExcecaoServicoWhatsApp(mensagem_erro) from e
    
    @staticmethod
    def _obter_config() -> dict:
        """Obtém configuração da API WhatsApp das settings."""
        config = getattr(settings, "META_API_SETTINGS", None)
        if not config:
            raise ExcecaoConfiguracao("META_API_SETTINGS não encontrado nas settings")
        return config
    
    @staticmethod
    def _validar_e_normalizar_telefone(cliente: Cliente) -> str:
        """Valida e normaliza número de telefone do cliente."""
        telefone_bruto = obter_atributo_seguro(cliente, "telefone_whatsapp")
        telefone_normalizado = normalizar_numero_telefone(telefone_bruto)
        
        if not telefone_normalizado:
            raise ExcecaoDadosInvalidos("Número de telefone inválido ou ausente")
        
        return telefone_normalizado
    
    @staticmethod
    def _encontrar_cobranca_associada(cliente: Cliente) -> Optional[Cobranca]:
        """Encontra a cobrança mais recente do cliente."""
        try:
            return Cobranca.objects.filter(cliente=cliente).order_by("-data_vencimento").first()
        except Exception:
            return None
    
    @staticmethod
    def _construir_url_api(config: dict) -> str:
        """Constrói URL da API WhatsApp."""
        url_base = config.get("URL_BASE", "")
        phone_id = config.get("PHONE_ID", "")
        
        base = url_base if str(url_base).endswith('/') else f"{url_base}/"
        return f"{base}{phone_id}/messages"
    
    @staticmethod
    def _construir_payload(numero_telefone: str, mensagem: str) -> dict:
        """Constrói payload da API WhatsApp."""
        return {
            "messaging_product": "whatsapp",
            "to": numero_telefone,
            "type": "text",
            "text": {"body": mensagem}
        }
    
    @staticmethod
    def _construir_headers(config: dict) -> dict:
        """Constrói headers HTTP para API WhatsApp."""
        token = config.get("TOKEN", "")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _enviar_com_tentativas(
        url: str,
        headers: dict,
        payload: dict,
        numero_telefone: str,
        mensagem: str,
        cobranca: Optional[Cobranca],
        tentativas_max: int,
        fator_backoff: float
    ) -> Tuple[bool, str]:
        """Envia mensagem com lógica de tentativas."""
        tentativa = 0
        ultimo_erro = None
        
        while tentativa < tentativas_max:
            tentativa += 1
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=TIMEOUT_REQUISICAO_SEGUNDOS
                )
                
                if response.status_code in CODIGOS_HTTP_SUCESSO:
                    ServicoWhatsApp._registrar_sucesso(cobranca, mensagem)
                    registrar_evento(
                        "info",
                        f"Mensagem WhatsApp enviada com sucesso para {numero_telefone}",
                        cliente_cpf=obter_atributo_seguro(cobranca, "cliente.cpf") if cobranca else None
                    )
                    return True, "ENVIADO"
                else:
                    ultimo_erro = f"Erro na API WhatsApp (Status: {response.status_code}, Resposta: {response.text[:200]})"
                    registrar_evento("warning", ultimo_erro, tentativa=tentativa, telefone=numero_telefone)
                    
            except requests.exceptions.RequestException as e:
                ultimo_erro = f"Erro de conexão (Tentativa {tentativa}): {e}"
                registrar_evento("error", ultimo_erro, tentativa=tentativa, telefone=numero_telefone)
            
            # Aguarda antes de tentar novamente se não for a última tentativa
            if tentativa < tentativas_max:
                tempo_espera = fator_backoff * (2 ** (tentativa - 1))
                time.sleep(tempo_espera)
        
        # Todas as tentativas falharam
        ServicoWhatsApp._registrar_falha(cobranca, mensagem, ultimo_erro)
        return False, ultimo_erro or "Erro desconhecido ao enviar WhatsApp"
    
    @staticmethod
    def _registrar_sucesso(cobranca: Optional[Cobranca], mensagem: str) -> None:
        """Registra notificação bem-sucedida."""
        if cobranca:
            ServicoNotificacao.criar_notificacao(
                cobranca=cobranca,
                tipo_regua="",
                canal=TipoCanal.WHATSAPP,
                conteudo=mensagem,
                status=StatusEnvio.ENVIADO
            )
    
    @staticmethod
    def _registrar_falha(
        cobranca: Optional[Cobranca],
        mensagem: str,
        erro: Optional[str]
    ) -> None:
        """Registra notificação com falha."""
        if cobranca:
            ServicoNotificacao.criar_notificacao(
                cobranca=cobranca,
                tipo_regua="",
                canal=TipoCanal.WHATSAPP,
                conteudo=mensagem,
                status=StatusEnvio.FALHA
            )

