"""
Serviço de cliente - Gerencia lógica de negócio de clientes.
Seguindo Single Responsibility: apenas operações relacionadas a cliente.
"""
from cobranca_app.models import Cliente
from cobranca_app.services.servico_cobranca import ServicoCobranca
from cobranca_app.core.excecoes import ExcecaoCliente
from cobranca_app.core.utilitarios import registrar_evento


class ServicoCliente:
    """Serviço para gerenciar clientes."""
    
    @staticmethod
    def criar_cliente_com_cobranca_inicial(cliente: Cliente) -> None:
        """
        Cria um cliente e gera sua primeira cobrança.
        
        Args:
            cliente: Instância do cliente a salvar
        
        Raises:
            ExcecaoCliente: Se a criação do cliente falhar
        """
        try:
            cliente.save()
            
            if cliente.plano:
                ServicoCobranca.criar_cobranca_inicial(cliente)
                registrar_evento("info", f"Cliente criado com cobrança inicial", cliente_cpf=cliente.cpf)
            else:
                registrar_evento("warning", f"Cliente criado sem plano", cliente_cpf=cliente.cpf)
                
        except Exception as e:
            registrar_evento("error", f"Falha ao criar cliente", cliente_cpf=getattr(cliente, "cpf", None))
            raise ExcecaoCliente(f"Erro ao criar cliente: {e}") from e

