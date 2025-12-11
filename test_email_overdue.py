#!/usr/bin/env python
"""
Script para testar envio de emails para clientes com pagamento atrasado.
Executa a rotina de cobrança manualmente e registra o resultado.
"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pilates_cobranca.settings')
django.setup()

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from cobranca_app.models import Cliente, Cobranca, Notificacao
from cobranca_app.services.servico_rotina_cobranca import RotinaDiariaCobranca
from cobranca_app.services.servico_email import ServicoEmail
from cobranca_app.core.constantes import StatusCobranca, StatusEnvio
from cobranca_app.core.utilitarios import registrar_evento


def testar_configuracao_email():
    """Testa se a configuração de email está correta."""
    print("\n" + "="*60)
    print("TESTANDO CONFIGURAÇÃO DE EMAIL")
    print("="*60)
    
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        send_mail(
            subject="Teste de Email - Sistema de Cobrança Pilates",
            message="Este é um email de teste do sistema de cobrança.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Enviar para si mesmo
            fail_silently=False,
        )
        print("✓ Email de teste enviado com sucesso!")
        return True
    except Exception as e:
        print(f"✗ Falha ao enviar email de teste: {e}")
        return False


def listar_cobrancas_atrasadas():
    """Lista todas as cobranças atrasadas no banco."""
    print("\n" + "="*60)
    print("COBRANÇAS ATRASADAS NO BANCO DE DADOS")
    print("="*60)
    
    cobrancas_atrasadas = Cobranca.objects.filter(
        status_cobranca=StatusCobranca.ATRASADO.value
    ).select_related('cliente')
    
    if not cobrancas_atrasadas.exists():
        print("Nenhuma cobrança atrasada encontrada.")
        print("\nGerando uma cobrança atrasada para teste...")
        return gerar_cobranca_teste()
    
    print(f"Total de cobranças atrasadas: {cobrancas_atrasadas.count()}\n")
    
    for cobranca in cobrancas_atrasadas:
        dias_atraso = cobranca.calcular_dias_atraso()
        print(f"  • {cobranca.cliente.nome}")
        print(f"    Email: {cobranca.cliente.email}")
        print(f"    Valor: R$ {cobranca.valor_total_devido}")
        print(f"    Vencimento: {cobranca.data_vencimento}")
        print(f"    Dias em atraso: {dias_atraso}")
        print()
    
    return cobrancas_atrasadas


def gerar_cobranca_teste():
    """Gera uma cobrança atrasada para teste."""
    print("Buscando clientes na base...")
    cliente = Cliente.objects.filter(status_cliente='ATIVO').first()
    
    if not cliente:
        print("✗ Nenhum cliente ativo encontrado!")
        print("Crie um cliente antes de executar este script.")
        return []
    
    # Verificar se já existe cobrança para este cliente
    ultima_cobranca = Cobranca.objects.filter(cliente=cliente).order_by('-data_vencimento').first()
    
    data_vencimento = timezone.localdate() - timedelta(days=5)  # 5 dias atrás
    referencia = data_vencimento.strftime('%m/%Y')
    
    # Verificar duplicata
    existe = Cobranca.objects.filter(
        cliente=cliente,
        data_vencimento=data_vencimento
    ).exists()
    
    if existe:
        print(f"Cobrança para {cliente.nome} em {data_vencimento} já existe.")
        cobrancas = Cobranca.objects.filter(
            cliente=cliente,
            data_vencimento=data_vencimento,
            status_cobranca=StatusCobranca.ATRASADO.value
        )
    else:
        cobranca = Cobranca.objects.create(
            cliente=cliente,
            valor_base=cliente.plano.valor_base if cliente.plano else Decimal('0.00'),
            valor_multa_juros=Decimal('0.00'),
            valor_total_devido=cliente.plano.valor_base if cliente.plano else Decimal('0.00'),
            data_vencimento=data_vencimento,
            referencia_ciclo=referencia,
            status_cobranca=StatusCobranca.ATRASADO.value
        )
        print(f"✓ Cobrança criada: {cobranca.cliente.nome} - R$ {cobranca.valor_total_devido}")
        cobrancas = [cobranca]
    
    return cobrancas


def executar_rotina():
    """Executa a rotina diária de cobrança."""
    print("\n" + "="*60)
    print("EXECUTANDO ROTINA DE COBRANÇA")
    print("="*60)
    
    try:
        resultado = RotinaDiariaCobranca.executar()
        print(f"✓ Rotina executada: {resultado}")
        return True
    except Exception as e:
        print(f"✗ Erro ao executar rotina: {e}")
        import traceback
        traceback.print_exc()
        return False


def listar_notificacoes():
    """Lista notificações de email enviadas/falhadas."""
    print("\n" + "="*60)
    print("NOTIFICAÇÕES RECENTES (EMAIL)")
    print("="*60)
    
    from cobranca_app.core.constantes import TipoCanal
    
    notificacoes = Notificacao.objects.filter(
        tipo_canal=TipoCanal.EMAIL
    ).order_by('-data_agendada')[:10]
    
    if not notificacoes.exists():
        print("Nenhuma notificação de email encontrada.")
        return
    
    print(f"Total de notificações listadas: {notificacoes.count()}\n")
    
    for notif in notificacoes:
        print(f"  • {notif.cobranca.cliente.nome}")
        print(f"    Status: {notif.status_envio}")
        print(f"    Tipo: {notif.tipo_regua}")
        print(f"    Data agendada: {notif.data_agendada}")
        if notif.data_envio_real:
            print(f"    Data envio real: {notif.data_envio_real}")
        print()


def main():
    """Função principal."""
    print("\n" + "█"*60)
    print("TESTE DE ENVIO DE EMAIL PARA CLIENTES COM ATRASO")
    print("█"*60)
    
    # 1. Testar configuração de email
    if not testar_configuracao_email():
        print("\n⚠️  Configuração de email inválida. Verifique settings.py")
        return
    
    # 2. Listar/gerar cobranças atrasadas
    cobrancas = listar_cobrancas_atrasadas()
    
    if not cobrancas:
        print("\n⚠️  Nenhuma cobrança atrasada para processar.")
        return
    
    # 3. Executar rotina de cobrança
    if not executar_rotina():
        print("\n⚠️  Rotina não foi executada.")
        return
    
    # 4. Listar notificações criadas
    listar_notificacoes()
    
    print("\n" + "█"*60)
    print("TESTE CONCLUÍDO")
    print("█"*60 + "\n")


if __name__ == '__main__':
    main()
