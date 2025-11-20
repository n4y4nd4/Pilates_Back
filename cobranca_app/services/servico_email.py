"""
Serviço de notificação por e-mail.
Seguindo Single Responsibility: apenas operações de envio de e-mail.
"""
import logging
from typing import Tuple
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from cobranca_app.models import Cobranca
from cobranca_app.core.constantes import StatusCobranca, FORMATO_DATA_EXIBICAO
from cobranca_app.core.utilitarios import registrar_evento, formatar_data_para_exibicao, obter_atributo_seguro
from cobranca_app.core.excecoes import ExcecaoServicoEmail, ExcecaoConfiguracao
from cobranca_app.core.validadores import validar_config_email

logger = logging.getLogger(__name__)


class ServicoEmail:
    """Serviço para enviar notificações por e-mail."""
    
    @staticmethod
    def enviar_notificacao_cobranca(
        cobranca: Cobranca,
        tipo_regua: str
    ) -> Tuple[bool, str]:
        """
        Envia e-mail de notificação de cobrança.
        
        Args:
            cobranca: Instância de cobrança
            tipo_regua: Tipo de regra de lembrete de pagamento
        
        Returns:
            Tupla de (sucesso: bool, detalhe: str)
        
        Raises:
            ExcecaoServicoEmail: Se o envio de e-mail falhar
            ExcecaoConfiguracao: Se a configuração de e-mail for inválida
        """
        try:
            validar_config_email()
            
            contexto = ServicoEmail._construir_contexto_email(cobranca)
            mensagem_html = render_to_string('cobranca_app/email_cobranca.html', contexto)
            
            assunto = f"Pilates - Aviso de Cobrança: {tipo_regua}"
            destinatario = cobranca.cliente.email
            
            send_mail(
                subject=assunto,
                message="Use um cliente de e-mail que suporte HTML.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                html_message=mensagem_html,
                fail_silently=False,
            )
            
            registrar_evento(
                "info",
                f"E-mail enviado com sucesso para {destinatario}",
                cobranca_id=cobranca.id,
                tipo_regua=tipo_regua
            )
            
            return True, "ENVIADO"
            
        except ExcecaoConfiguracao:
            raise
        except Exception as e:
            mensagem_erro = f"Falha ao enviar e-mail: {e}"
            registrar_evento(
                "error",
                mensagem_erro,
                cobranca_id=obter_atributo_seguro(cobranca, "id"),
                tipo_regua=tipo_regua
            )
            raise ExcecaoServicoEmail(mensagem_erro) from e
    
    @staticmethod
    def _construir_contexto_email(cobranca: Cobranca) -> dict:
        """
        Constrói o contexto do template de e-mail.
        
        Args:
            cobranca: Instância de cobrança
        
        Returns:
            Dicionário com contexto do template
        """
        status_cobranca = obter_atributo_seguro(cobranca, "status_cobranca", "")
        esta_atrasado = status_cobranca == StatusCobranca.ATRASADO.value
        
        return {
            'nome_cliente': cobranca.cliente.nome,
            'valor_total': cobranca.valor_total_devido,
            'data_vencimento': formatar_data_para_exibicao(cobranca.data_vencimento),
            'status_cobranca': "Em Atraso" if esta_atrasado else "Lembrete",
            'ciclo_referencia': obter_atributo_seguro(cobranca, "referencia_ciclo", ""),
        }


