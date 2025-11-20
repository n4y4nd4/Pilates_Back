"""
Funções utilitárias compartilhadas.
Seguindo princípio DRY: funções reutilizáveis usadas em toda a aplicação.
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from datetime import date, timedelta

logger = logging.getLogger(__name__)


def calcular_data_vencimento(
    data_inicio: date,
    periodicidade_meses: int,
    dias_por_mes: int = 30
) -> date:
    """
    Calcula a data de vencimento com base na data de início e periodicidade.
    
    Args:
        data_inicio: Data de início do contrato
        periodicidade_meses: Número de meses no período de cobrança
        dias_por_mes: Dias a considerar por mês (padrão: 30)
    
    Returns:
        Data de vencimento calculada
    """
    data_calculada = data_inicio + timedelta(days=periodicidade_meses * dias_por_mes)
    hoje = timezone.localdate()
    
    # Se a data calculada está no passado, calcula a partir de hoje
    if data_calculada < hoje:
        return hoje + timedelta(days=periodicidade_meses * dias_por_mes)
    
    return data_calculada


def formatar_data_para_exibicao(data_valor: Optional[date]) -> str:
    """
    Formata uma data para exibição.
    
    Args:
        data_valor: Data a formatar
    
    Returns:
        String de data formatada ou string vazia se None
    """
    if not data_valor:
        return ""
    return data_valor.strftime("%d/%m/%Y")


def registrar_evento(
    nivel: str,
    mensagem: str,
    instancia_logger: Optional[logging.Logger] = None,
    **metadados: Any
) -> None:
    """
    Registra um evento com metadados estruturados.
    
    Args:
        nivel: Nível de log (info, warning, error, etc.)
        mensagem: Mensagem legível
        instancia_logger: Instância do logger (padrão: logger do módulo)
        **metadados: Metadados adicionais para log
    """
    log = instancia_logger or logger
    
    try:
        # Log da mensagem legível
        getattr(log, nivel)(mensagem)
        
        # Log de metadados estruturados
        dados_estruturados = {
            "timestamp": timezone.now().isoformat(),
            "mensagem": mensagem,
            "metadados": metadados
        }
        log.info(f"STRUCTURED_LOG: {dados_estruturados}")
    except Exception as e:
        log.exception(f"Erro ao registrar evento: {e}")


def normalizar_numero_telefone(numero_telefone: Optional[str]) -> str:
    """
    Normaliza número de telefone para apenas dígitos.
    
    Args:
        numero_telefone: String de número de telefone bruto
    
    Returns:
        Número de telefone normalizado (apenas dígitos)
    
    Exemplo:
        "+55 (21) 9 8765-4321" -> "5521987654321"
    """
    if not numero_telefone:
        return ""
    return "".join(char for char in str(numero_telefone) if char.isdigit())


def obter_atributo_seguro(obj: Any, atributo: str, padrao: Any = None) -> Any:
    """
    Obtém um atributo de um objeto de forma segura.
    
    Args:
        obj: Objeto do qual obter o atributo
        atributo: Nome do atributo
        padrao: Valor padrão se o atributo não existir
    
    Returns:
        Valor do atributo ou padrão
    """
    return getattr(obj, atributo, padrao)


