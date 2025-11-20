"""
Constantes usadas em toda a aplicação.
Seguindo princípios de Clean Code: sem números ou strings mágicas.
"""
from enum import Enum
from datetime import timedelta


class StatusCliente(str, Enum):
    """Opções de status do cliente."""
    ATIVO = 'ATIVO'
    INATIVO_ATRASO = 'INATIVO_ATRASO'
    INATIVO_MANUAL = 'INATIVO_MANUAL'


class StatusCobranca(str, Enum):
    """Opções de status da cobrança."""
    PENDENTE = 'PENDENTE'
    PAGO = 'PAGO'
    ATRASADO = 'ATRASADO'
    CANCELADO = 'CANCELADO'


class StatusEnvio(str, Enum):
    """Opções de status de envio de notificação."""
    AGENDADO = 'AGENDADO'
    ENVIADO = 'ENVIADO'
    FALHA = 'FALHA'


class TipoCanal(str, Enum):
    """Tipos de canais de notificação."""
    EMAIL = 'Email'
    WHATSAPP = 'WhatsApp'


class TipoRegua(str, Enum):
    """Tipos de regras de lembrete de pagamento."""
    LEMBRETE_D3 = 'Lembrete (D-3)'
    ATRASO_D1 = 'Atraso (D+1)'
    AVISO_BLOQUEIO_D10 = 'Aviso de Bloqueio (D+10)'


# Constantes de Regras de Negócio
DIAS_POR_MES = 30
DIAS_ANTES_VENCIMENTO_LEMBRETE = 3
DIAS_APOS_VENCIMENTO_AVISO_1 = 1
DIAS_APOS_VENCIMENTO_AVISO_2 = 10

# Constantes da API WhatsApp
TAMANHO_MIN_TOKEN = 30
TENTATIVAS_MAX_PADRAO = 3
FATOR_BACKOFF_PADRAO = 1.0
TIMEOUT_REQUISICAO_SEGUNDOS = 12

# Constantes de Formato de Data
FORMATO_DATA_EXIBICAO = "%d/%m/%Y"
FORMATO_DATA_REFERENCIA = "%Y-%m"

# Códigos de Status HTTP
CODIGOS_HTTP_SUCESSO = (200, 201)

