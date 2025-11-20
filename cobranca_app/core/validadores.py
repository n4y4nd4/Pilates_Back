"""
Funções de validação para regras de negócio.
Seguindo Single Responsibility: cada validador tem um propósito claro.
"""
import re
from typing import Optional
from cobranca_app.core.excecoes import ExcecaoDadosInvalidos, ExcecaoConfiguracao
from cobranca_app.core.constantes import TAMANHO_MIN_TOKEN


def validar_numero_telefone(numero_telefone: Optional[str]) -> None:
    """
    Valida o formato do número de telefone.
    
    Args:
        numero_telefone: Número de telefone a validar
    
    Raises:
        ExcecaoDadosInvalidos: Se o número de telefone for inválido
    """
    if not numero_telefone:
        raise ExcecaoDadosInvalidos("Número de telefone é obrigatório")
    
    apenas_digitos = "".join(char for char in str(numero_telefone) if char.isdigit())
    if len(apenas_digitos) < 10:
        raise ExcecaoDadosInvalidos("Número de telefone deve ter pelo menos 10 dígitos")


def validar_config_whatsapp(config: dict) -> None:
    """
    Valida a configuração da API WhatsApp.
    
    Args:
        config: Dicionário de configuração
    
    Raises:
        ExcecaoConfiguracao: Se a configuração for inválida
    """
    if not config:
        raise ExcecaoConfiguracao("Configuração META_API_SETTINGS não encontrada")
    
    token = config.get("TOKEN")
    phone_id = config.get("PHONE_ID")
    url_base = config.get("URL_BASE")
    
    if not token or not phone_id or not url_base:
        raise ExcecaoConfiguracao("Configuração WhatsApp incompleta: TOKEN, PHONE_ID ou URL_BASE faltando")
    
    if len(str(token)) < TAMANHO_MIN_TOKEN:
        raise ExcecaoConfiguracao(f"Token deve ter pelo menos {TAMANHO_MIN_TOKEN} caracteres")


def validar_config_email() -> None:
    """
    Valida a configuração de e-mail.
    
    Raises:
        ExcecaoConfiguracao: Se a configuração de e-mail for inválida
    """
    from django.conf import settings
    
    configuracoes_obrigatorias = [
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL'
    ]
    
    faltando = [config for config in configuracoes_obrigatorias if not getattr(settings, config, None)]
    
    if faltando:
        raise ExcecaoConfiguracao(f"Configuração de e-mail incompleta: {', '.join(faltando)}")


def validar_cpf(cpf: Optional[str]) -> str:
    """
    Valida e normaliza CPF brasileiro.
    
    Args:
        cpf: CPF a validar (pode conter pontos e traço)
    
    Returns:
        CPF normalizado (apenas dígitos)
    
    Raises:
        ExcecaoDadosInvalidos: Se o CPF for inválido
    """
    if not cpf:
        raise ExcecaoDadosInvalidos("CPF é obrigatório")
    
    # Remove caracteres não numéricos
    cpf_numeros = re.sub(r'[^0-9]', '', str(cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf_numeros) != 11:
        raise ExcecaoDadosInvalidos("CPF deve conter 11 dígitos")
    
    # Verifica se todos os dígitos são iguais (CPF inválido)
    if cpf_numeros == cpf_numeros[0] * 11:
        raise ExcecaoDadosInvalidos("CPF inválido: todos os dígitos são iguais")
    
    # Validação dos dígitos verificadores
    def calcular_digito(cpf_parcial: str, peso_inicial: int) -> int:
        soma = sum(int(cpf_parcial[i]) * (peso_inicial - i) for i in range(len(cpf_parcial)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    # Valida primeiro dígito verificador
    primeiro_digito = calcular_digito(cpf_numeros[:9], 10)
    if primeiro_digito != int(cpf_numeros[9]):
        raise ExcecaoDadosInvalidos("CPF inválido: primeiro dígito verificador incorreto")
    
    # Valida segundo dígito verificador
    segundo_digito = calcular_digito(cpf_numeros[:10], 11)
    if segundo_digito != int(cpf_numeros[10]):
        raise ExcecaoDadosInvalidos("CPF inválido: segundo dígito verificador incorreto")
    
    return cpf_numeros


def validar_email_unico(email: str, cliente_cpf: Optional[str] = None) -> None:
    """
    Valida se o e-mail é único no banco de dados.
    
    Args:
        email: E-mail a validar
        cliente_cpf: CPF do cliente atual (para permitir atualização do próprio registro)
    
    Raises:
        ExcecaoDadosInvalidos: Se o e-mail já estiver em uso
    """
    from cobranca_app.models import Cliente
    
    if not email:
        raise ExcecaoDadosInvalidos("E-mail é obrigatório")
    
    # Valida formato básico de e-mail
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ExcecaoDadosInvalidos("Formato de e-mail inválido. Use o formato: exemplo@dominio.com")
    
    # Verifica se já existe outro cliente com este e-mail
    query = Cliente.objects.filter(email__iexact=email)
    if cliente_cpf:
        query = query.exclude(cpf=cliente_cpf)
    
    if query.exists():
        raise ExcecaoDadosInvalidos("Este e-mail já está cadastrado para outro cliente")


def validar_telefone_unico(telefone: str, cliente_cpf: Optional[str] = None) -> None:
    """
    Valida se o telefone é único no banco de dados.
    
    Args:
        telefone: Telefone a validar
        cliente_cpf: CPF do cliente atual (para permitir atualização do próprio registro)
    
    Raises:
        ExcecaoDadosInvalidos: Se o telefone já estiver em uso
    """
    from cobranca_app.models import Cliente
    from cobranca_app.core.utilitarios import normalizar_numero_telefone
    
    if not telefone:
        raise ExcecaoDadosInvalidos("Telefone é obrigatório")
    
    # Normaliza o telefone (remove caracteres não numéricos)
    telefone_normalizado = normalizar_numero_telefone(telefone)
    
    # Valida formato
    validar_numero_telefone(telefone_normalizado)
    
    # Verifica se já existe outro cliente com este telefone
    # Normaliza todos os telefones no banco para comparação
    clientes = Cliente.objects.all()
    if cliente_cpf:
        clientes = clientes.exclude(cpf=cliente_cpf)
    
    for cliente in clientes:
        telefone_cliente_normalizado = normalizar_numero_telefone(cliente.telefone_whatsapp)
        if telefone_normalizado == telefone_cliente_normalizado:
            raise ExcecaoDadosInvalidos("Este telefone já está cadastrado para outro cliente")


def validar_cpf_unico(cpf: str, cliente_cpf_atual: Optional[str] = None) -> None:
    """
    Valida se o CPF é único no banco de dados.
    
    Args:
        cpf: CPF a validar (já normalizado)
        cliente_cpf_atual: CPF do cliente atual (para permitir atualização do próprio registro)
    
    Raises:
        ExcecaoDadosInvalidos: Se o CPF já estiver em uso
    """
    from cobranca_app.models import Cliente
    
    if not cpf:
        raise ExcecaoDadosInvalidos("CPF é obrigatório")
    
    # Se estiver atualizando o mesmo CPF, não precisa verificar
    if cliente_cpf_atual and cpf == cliente_cpf_atual:
        return
    
    # Verifica se já existe outro cliente com este CPF
    if Cliente.objects.filter(cpf=cpf).exists():
        raise ExcecaoDadosInvalidos("Este CPF já está cadastrado para outro cliente")

