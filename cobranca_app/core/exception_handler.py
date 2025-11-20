"""
Exception handler customizado para o DRF.
Converte exceções customizadas em respostas HTTP adequadas.
NÃO interfere com ValidationErrors do DRF - permite que erros por campo sejam retornados.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from cobranca_app.core.excecoes import (
    ExcecaoDadosInvalidos,
    ExcecaoConfiguracao,
    ExcecaoCliente,
    ExcecaoCobrancaOperacao,
    ExcecaoNotificacao
)


def excecao_handler_customizado(exc, context):
    """
    Handler customizado de exceções para o DRF.
    
    IMPORTANTE: Não interfere com ValidationErrors do DRF.
    O DRF já trata ValidationError automaticamente e retorna erros por campo.
    
    Converte apenas exceções customizadas que não são ValidationErrors:
    - ExcecaoConfiguracao -> 500 Internal Server Error
    - Outras exceções customizadas não tratadas -> 500 Internal Server Error
    """
    # Primeiro, tenta o handler padrão do DRF
    # Isso já trata ValidationError e retorna erros por campo automaticamente
    response = exception_handler(exc, context)
    
    # Se o handler padrão retornou uma resposta, usa ela (inclui ValidationErrors)
    if response is not None:
        return response
    
    # Se o handler padrão não conseguiu tratar, trata apenas exceções customizadas
    # que não são ValidationErrors (que já foram tratadas acima)
    if isinstance(exc, ExcecaoConfiguracao):
        response = Response(
            {'error': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    elif isinstance(exc, (ExcecaoCliente, ExcecaoCobrancaOperacao, ExcecaoNotificacao)):
        # Exceções de negócio que não são ValidationErrors
        response = Response(
            {'error': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )
    elif isinstance(exc, ExcecaoDadosInvalidos):
        # ExcecaoDadosInvalidos deve ser convertida em ValidationError no serializer
        # Se chegou aqui, algo deu errado - retorna como erro genérico
        response = Response(
            {'error': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )
    else:
        # Para qualquer outra exceção não tratada, retorna erro 500
        from django.conf import settings
        if settings.DEBUG:
            mensagem_erro = f"Erro interno do servidor: {str(exc)}"
        else:
            mensagem_erro = "Erro interno do servidor. Verifique os logs do backend."
        
        response = Response(
            {'error': mensagem_erro},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response

