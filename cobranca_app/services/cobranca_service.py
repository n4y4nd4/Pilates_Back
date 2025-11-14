# cobranca_app/services/cobranca_service.py
"""
Lógica da régua de cobrança (D-3, D0, D+1..D+N).
Chama os services de notificação (WhatsApp + Email) e cria registros em Notificacao.
"""

from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import logging

from cobranca_app.models import Cobranca, Notificacao, Cliente
from cobranca_app.services.whatsapp_service import enviar_whatsapp_real
from cobranca_app.services.email_service import enviar_email_real

logger = logging.getLogger(__name__)


def _log(msg, **meta):
    logger.info(msg + " | " + str(meta))


def _get_or_create_placeholder_cobranca(cliente):
    """
    Se não existir uma cobranca relacionada, cria uma cobranca 'placeholder' mínima
    para que possamos registrar Notificacao (evita NOT NULL constraint).
    Essa cobranca tem valores zeros e data de vencimento hoje.
    """
    latest = Cobranca.objects.filter(cliente=cliente).order_by("-data_vencimento").first()
    if latest:
        return latest

    # criar placeholder
    today = timezone.localdate()
    referencia = today.strftime("%Y-%m")
    placeholder = Cobranca.objects.create(
        cliente=cliente,
        valor_base=Decimal('0.00'),
        valor_multa_juros=Decimal('0.00'),
        valor_total_devido=Decimal('0.00'),
        data_vencimento=today,
        referencia_ciclo=referencia,
        status_cobranca='PENDENTE'
    )
    return placeholder


def _criar_notificacao(cobranca_obj, tipo_regua, canal, conteudo, status_envio):
    """
    Cria um registro de Notificacao no BD.
    """
    try:
        Notificacao.objects.create(
            cobranca=cobranca_obj,
            tipo_regua=tipo_regua,
            tipo_canal=canal,
            conteudo_mensagem=conteudo,
            data_agendada=timezone.now(),
            data_envio_real=timezone.now(),
            status_envio=status_envio
        )
    except Exception as e:
        # Log e segue em frente
        _log("Erro ao criar Notificacao no banco", exception=str(e), cobranca_id=getattr(cobranca_obj, "id", None))


def rotina_diaria_disparo():
    """
    Função principal da rotina. Mantém a mesma lógica que você tinha no tasks.py,
    mas agora organiza e chama os services (whatsapp + email).
    """
    hoje = timezone.localdate()
    print(f"--- INICIANDO ROTINA DE COBRANCA: {hoje} ---")

    # 1) Marca ATRASADO
    num_atrasados = Cobranca.objects.filter(status_cobranca='PENDENTE', data_vencimento__lt=hoje).update(status_cobranca='ATRASADO')
    print(f"  -> {num_atrasados} cobranças foram marcadas como ATRASADAS.")

    # 2) Define lembretes D-3 e cobranças em atraso
    data_lembrete = hoje + timedelta(days=3)

    cobrancas_a_lembrar = Cobranca.objects.filter(status_cobranca='PENDENTE', data_vencimento=data_lembrete).select_related('cliente')
    cobrancas_em_atraso = Cobranca.objects.filter(status_cobranca='ATRASADO').select_related('cliente')

    cobrancas_elegiveis = list(cobrancas_a_lembrar) + list(cobrancas_em_atraso)

    for cobranca in cobrancas_elegiveis:
        cliente = cobranca.cliente
        # tipo_regua e conteudo conforme sua lógica original
        if cobranca.status_cobranca == 'ATRASADO':
            dias_atraso = (hoje - cobranca.data_vencimento).days
            if dias_atraso == 1:
                tipo_regua = 'Atraso (D+1)'
            elif dias_atraso == 10:
                tipo_regua = 'Aviso de Bloqueio (D+10)'
            else:
                tipo_regua = f'Atraso (D+{dias_atraso} dias)'
            conteudo = f"ATRASO: {cliente.nome}, sua cobrança de R$ {cobranca.valor_total_devido} está atrasada em {dias_atraso} dias."
        elif cobranca.data_vencimento == data_lembrete:
            tipo_regua = 'Lembrete (D-3)'
            conteudo = f"Olá {cliente.nome}, sua cobrança de R$ {cobranca.valor_total_devido} vencerá em 3 dias ({cobranca.data_vencimento})."
        else:
            tipo_regua = 'Erro/Outro'
            conteudo = "Erro na definição da régua."

        print(f"  -> Disparando {tipo_regua} para {cliente.nome}")

        # Tenta enviar WhatsApp (service separado)
        sucesso_wa, detalhe_wa = enviar_whatsapp_real(cliente, conteudo)
        # Tenta enviar Email (service separado)
        sucesso_email, detalhe_email = enviar_email_real(cobranca, tipo_regua)

        # Garantir que exista uma cobranca para anexar na Notificacao (placeholder se necessário)
        cobranca_obj_para_registro = cobranca or _get_or_create_placeholder_cobranca(cliente)

        # Registrar Notificações (1 por canal) sempre (opção A)
        status_wa = "ENVIADO" if sucesso_wa else "FALHA"
        status_email = "ENVIADO" if sucesso_email else "FALHA"

        _criar_notificacao(cobranca_obj_para_registro, tipo_regua, "WhatsApp", conteudo, status_wa)
        _criar_notificacao(cobranca_obj_para_registro, tipo_regua, "Email", conteudo, status_email)

    print("--- ROTINA CONCLUÍDA ---")
    return "Disparos e Atualizações Concluídas."
