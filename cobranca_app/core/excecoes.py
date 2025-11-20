"""
Exceções personalizadas para a aplicação de cobrança.
Seguindo Clean Code: exceções específicas para melhor tratamento de erros.
"""


class ExcecaoCobranca(Exception):
    """Exceção base para erros relacionados a cobrança."""
    pass


class ExcecaoCliente(ExcecaoCobranca):
    """Exceção relacionada a operações de cliente."""
    pass


class ExcecaoCobrancaOperacao(ExcecaoCobranca):
    """Exceção relacionada a operações de cobrança."""
    pass


class ExcecaoNotificacao(ExcecaoCobranca):
    """Exceção relacionada a operações de notificação."""
    pass


class ExcecaoServicoEmail(ExcecaoNotificacao):
    """Exceção relacionada ao envio de e-mail."""
    pass


class ExcecaoServicoWhatsApp(ExcecaoNotificacao):
    """Exceção relacionada ao envio de WhatsApp."""
    pass


class ExcecaoConfiguracao(ExcecaoCobranca):
    """Exceção relacionada a erros de configuração."""
    pass


class ExcecaoDadosInvalidos(ExcecaoCobranca):
    """Exceção para validação de dados inválidos."""
    pass


