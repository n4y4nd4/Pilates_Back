"""
Serviço de rotina diária de cobrança.
Orquestra o processo diário de notificação de cobranças.
Seguindo Clean Code: responsabilidade única, funções pequenas, nomes claros.
"""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from cobranca_app.models import Cobranca
from cobranca_app.core.constantes import (
    TipoCanal,
    StatusEnvio,
    DIAS_ANTES_VENCIMENTO_LEMBRETE
)
from cobranca_app.core.utilitarios import registrar_evento
from cobranca_app.services.servico_cobranca import ServicoCobranca
from cobranca_app.services.construtor_mensagem import ConstrutorMensagem
from cobranca_app.services.servico_email import ServicoEmail
from cobranca_app.services.servico_whatsapp import ServicoWhatsApp
from cobranca_app.services.servico_notificacao import ServicoNotificacao


class RotinaDiariaCobranca:
    """Serviço para executar rotina diária de notificação de cobranças."""
    
    @staticmethod
    def executar() -> str:
        """
        Executa a rotina diária de notificação de cobranças.
        
        Returns:
            Mensagem de status
        """
        hoje = timezone.localdate()
        registrar_evento("info", f"Iniciando rotina diária de cobrança: {hoje}")
        
        # Passo 1: Marcar cobranças atrasadas
        quantidade_atrasadas = RotinaDiariaCobranca._marcar_cobrancas_atrasadas()
        registrar_evento("info", f"Marcadas {quantidade_atrasadas} cobranças como atrasadas")
        
        # Passo 2: Obter cobranças elegíveis para notificações
        cobrancas_elegiveis = RotinaDiariaCobranca._obter_cobrancas_elegiveis(hoje)
        registrar_evento("info", f"Encontradas {len(cobrancas_elegiveis)} cobranças elegíveis para notificação")
        
        # Passo 3: Processar cada cobrança
        for cobranca in cobrancas_elegiveis:
            RotinaDiariaCobranca._processar_notificacao_cobranca(cobranca, hoje)
        
        registrar_evento("info", "Rotina diária de cobrança concluída")
        return "Disparos e Atualizações Concluídas."
    
    @staticmethod
    def _marcar_cobrancas_atrasadas() -> int:
        """Marca cobranças pendentes como atrasadas."""
        return ServicoCobranca.marcar_cobrancas_atrasadas()
    
    @staticmethod
    def _obter_cobrancas_elegiveis(hoje) -> list:
        """
        Obtém cobranças elegíveis para notificação.
        
        Args:
            hoje: Data atual
        
        Returns:
            Lista de instâncias de Cobranca elegíveis
        """
        data_lembrete = hoje + timedelta(days=DIAS_ANTES_VENCIMENTO_LEMBRETE)
        
        cobrancas_lembrete = ServicoCobranca.obter_cobrancas_para_lembrete(data_lembrete)
        cobrancas_atrasadas = ServicoCobranca.obter_cobrancas_atrasadas()
        
        return cobrancas_lembrete + cobrancas_atrasadas
    
    @staticmethod
    def _processar_notificacao_cobranca(cobranca: Cobranca, hoje) -> None:
        """
        Processa notificação para uma única cobrança.
        
        Args:
            cobranca: Instância de cobrança
            hoje: Data atual
        """
        cliente = cobranca.cliente
        tipo_regua, conteudo = RotinaDiariaCobranca._construir_mensagem(cobranca, hoje)
        
        registrar_evento("info", f"Enviando {tipo_regua} para {cliente.nome}")
        
        # Enviar notificações
        resultado_whatsapp = RotinaDiariaCobranca._enviar_notificacao_whatsapp(
            cliente, conteudo, tipo_regua
        )
        resultado_email = RotinaDiariaCobranca._enviar_notificacao_email(
            cobranca, tipo_regua, conteudo
        )
        
        # Registrar notificações
        RotinaDiariaCobranca._registrar_notificacoes(
            cobranca=cobranca,
            tipo_regua=tipo_regua,
            conteudo=conteudo,
            sucesso_whatsapp=resultado_whatsapp[0],
            sucesso_email=resultado_email[0]
        )
    
    @staticmethod
    def _construir_mensagem(cobranca: Cobranca, hoje) -> tuple:
        """
        Constrói mensagem de notificação com base no status da cobrança.
        
        Args:
            cobranca: Instância de cobrança
            hoje: Data atual
        
        Returns:
            Tupla de (tipo_regua, conteudo_mensagem)
        """
        if cobranca.is_atrasado():
            dias_atraso = cobranca.calcular_dias_atraso()
            return ConstrutorMensagem.construir_mensagem_atraso(cobranca, dias_atraso)
        else:
            return ConstrutorMensagem.construir_mensagem_lembrete(cobranca)
    
    @staticmethod
    def _enviar_notificacao_whatsapp(
        cliente,
        conteudo: str,
        tipo_regua: str
    ) -> tuple:
        """
        Envia notificação WhatsApp se habilitada.
        
        Args:
            cliente: Instância do cliente
            conteudo: Conteúdo da mensagem
            tipo_regua: Tipo de regra de lembrete
        
        Returns:
            Tupla de (sucesso: bool, detalhe: str)
        """
        if not RotinaDiariaCobranca._whatsapp_habilitado():
            registrar_evento(
                "info",
                f"WhatsApp desabilitado para {cliente.nome} (kill switch)",
                cliente_cpf=cliente.cpf,
                tipo_regua=tipo_regua
            )
            return False, "Desativado por chave de configuração."
        
        try:
            return ServicoWhatsApp.enviar_mensagem(cliente, conteudo)
        except Exception as e:
            registrar_evento("error", f"Falha ao enviar WhatsApp: {e}", cliente_cpf=cliente.cpf)
            return False, str(e)
    
    @staticmethod
    def _enviar_notificacao_email(cobranca: Cobranca, tipo_regua: str, conteudo: str) -> tuple:
        """
        Envia notificação por e-mail.
        
        Args:
            cobranca: Instância de cobrança
            tipo_regua: Tipo de regra de lembrete
            conteudo: Conteúdo da mensagem
        
        Returns:
            Tupla de (sucesso: bool, detalhe: str)
        """
        try:
            return ServicoEmail.enviar_notificacao_cobranca(cobranca, tipo_regua, conteudo)
        except Exception as e:
            registrar_evento("error", f"Falha ao enviar e-mail: {e}", cobranca_id=cobranca.id)
            return False, str(e)    
    @staticmethod
    def _whatsapp_habilitado() -> bool:
        """Verifica se notificações WhatsApp estão habilitadas."""
        meta_cfg = getattr(settings, "META_API_SETTINGS", {})
        return meta_cfg.get("WHATSAPP_ENABLED", True)
    
    @staticmethod
    def _registrar_notificacoes(
        cobranca: Cobranca,
        tipo_regua: str,
        conteudo: str,
        sucesso_whatsapp: bool,
        sucesso_email: bool
    ) -> None:
        """
        Registra tentativas de notificação no banco de dados.
        
        Args:
            cobranca: Instância de cobrança
            tipo_regua: Tipo de regra de lembrete
            conteudo: Conteúdo da mensagem
            sucesso_whatsapp: Resultado do envio WhatsApp
            sucesso_email: Resultado do envio de e-mail
        """
        # Garantir que temos uma cobrança para notificação
        cobranca_para_notificacao = cobranca or ServicoNotificacao.obter_ou_criar_cobranca_placeholder(
            cobranca.cliente
        )
        
        # Registrar notificação WhatsApp
        status_whatsapp = StatusEnvio.ENVIADO if sucesso_whatsapp else StatusEnvio.FALHA
        ServicoNotificacao.criar_notificacao(
            cobranca=cobranca_para_notificacao,
            tipo_regua=tipo_regua,
            canal=TipoCanal.WHATSAPP,
            conteudo=conteudo,
            status=status_whatsapp
        )
        
        # Notificação de E-mail agora é registrada internamente pelo ServicoEmail
        # para garantir que qualquer envio de email (mesmo fora da rotina) seja logado.


# Função de compatibilidade retroativa
def rotina_diaria_disparo() -> str:
    """
    Função legada para compatibilidade retroativa.
    
    Returns:
        Mensagem de status
    """
    return RotinaDiariaCobranca.executar()

