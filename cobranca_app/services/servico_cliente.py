"""
Serviço de cliente - Gerencia lógica de negócio de clientes.
Seguindo Single Responsibility: apenas operações relacionadas a cliente.
"""
from django.utils import timezone
from cobranca_app.models import Cliente
from cobranca_app.services.servico_cobranca import ServicoCobranca
from cobranca_app.services.servico_email import ServicoEmail
from cobranca_app.services.construtor_mensagem import ConstrutorMensagem
from cobranca_app.core.constantes import StatusCobranca
from cobranca_app.core.excecoes import ExcecaoCliente
from cobranca_app.core.utilitarios import registrar_evento


class ServicoCliente:
    """Serviço para gerenciar clientes."""
    
    @staticmethod
    def criar_cliente_com_cobranca_inicial(cliente: Cliente) -> None:
        """
        Cria um cliente e gera sua primeira cobrança.
        Se a cobrança for criada como atrasada, envia email imediatamente.
        
        Args:
            cliente: Instância do cliente a salvar
        
        Raises:
            ExcecaoCliente: Se a criação do cliente falhar
        """
        try:
            cliente.save()
            
            if cliente.plano:
                cobranca = ServicoCobranca.criar_cobranca_inicial(cliente)
                registrar_evento("info", f"Cliente criado com cobrança inicial", cliente_cpf=cliente.cpf)
                
                # Se a cobrança foi criada como atrasada, envia email imediatamente
                if cobranca.status_cobranca == StatusCobranca.ATRASADO.value:
                    try:
                        dias_atraso = cobranca.calcular_dias_atraso()
                        tipo_regua, conteudo_mensagem = ConstrutorMensagem.construir_mensagem_atraso(cobranca, dias_atraso)
                        ServicoEmail.enviar_notificacao_cobranca(cobranca, tipo_regua, conteudo_mensagem)
                        registrar_evento(
                            "info",
                            f"Email de cobrança atrasada enviado imediatamente para {cliente.nome}",
                            cliente_cpf=cliente.cpf,
                            tipo_regua=tipo_regua
                        )
                    except Exception as e:
                        # Não falha a criação do cliente se o email falhar
                        registrar_evento(
                            "warning",
                            f"Cliente criado mas falha ao enviar email de cobrança atrasada: {e}",
                            cliente_cpf=cliente.cpf
                        )
            else:
                registrar_evento("warning", f"Cliente criado sem plano", cliente_cpf=cliente.cpf)
                
        except Exception as e:
            registrar_evento("error", f"Falha ao criar cliente", cliente_cpf=getattr(cliente, "cpf", None))
            raise ExcecaoCliente(f"Erro ao criar cliente: {e}") from e

