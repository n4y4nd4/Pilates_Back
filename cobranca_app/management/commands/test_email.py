"""
Management command to test email sending functionality.
Following Clean Code: clear command structure and error handling.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from cobranca_app.models import Cliente, Cobranca, Plano
from cobranca_app.services.email_service import EmailService
from cobranca_app.services.billing_service import BillingService
from cobranca_app.core.constants import DAYS_BEFORE_DUE_REMINDER


class Command(BaseCommand):
    """Command to test email sending."""
    
    help = "Testa o envio de e-mail criando dados de teste e enviando um e-mail."
    
    TEST_EMAIL = 'nayanda.robers@gmail.com'
    TEST_PLAN_NAME = "Plano Mensal Teste"
    TEST_CLIENT_NAME = "Cliente Teste"
    TEST_CPF = "12345678901"
    TEST_PHONE = "5521999999999"
    
    def handle(self, *args, **options) -> None:
        """Execute the email test command."""
        self.stdout.write(self.style.SUCCESS('=== TESTE DE ENVIO DE E-MAIL ===\n'))
        
        plano = self._get_or_create_test_plan()
        cliente = self._get_or_create_test_client(plano)
        cobranca = self._get_or_create_test_billing(cliente, plano)
        
        self._test_email_sending(cobranca)
        
        self.stdout.write(self.style.SUCCESS('\n=== TESTE CONCLUÍDO ==='))
    
    def _get_or_create_test_plan(self) -> Plano:
        """Get or create a test plan."""
        plano = Plano.objects.first()
        if not plano:
            self.stdout.write(self.style.WARNING('Criando plano de teste...'))
            plano = Plano.objects.create(
                nome_plano=self.TEST_PLAN_NAME,
                valor_base=Decimal('150.00'),
                periodicidade_meses=1,
                ativo=True
            )
            self.stdout.write(self.style.SUCCESS(f'Plano criado: {plano.nome_plano}'))
        return plano
    
    def _get_or_create_test_client(self, plano: Plano) -> Cliente:
        """Get or create a test client."""
        cliente = Cliente.objects.filter(email=self.TEST_EMAIL).first()
        if not cliente:
            self.stdout.write(self.style.WARNING('Criando cliente de teste...'))
            cliente = Cliente.objects.create(
                plano=plano,
                nome=self.TEST_CLIENT_NAME,
                cpf=self.TEST_CPF,
                telefone_whatsapp=self.TEST_PHONE,
                email=self.TEST_EMAIL,
                data_inicio_contrato=timezone.localdate(),
                status_cliente='ATIVO'
            )
            self.stdout.write(self.style.SUCCESS(f'Cliente criado: {cliente.nome}'))
        return cliente
    
    def _get_or_create_test_billing(self, cliente: Cliente, plano: Plano) -> Cobranca:
        """Get or create a test billing."""
        cobranca = Cobranca.objects.filter(cliente=cliente).first()
        if not cobranca:
            self.stdout.write(self.style.WARNING('Criando cobrança de teste...'))
            data_vencimento = timezone.localdate() + timedelta(days=DAYS_BEFORE_DUE_REMINDER)
            cobranca = Cobranca.objects.create(
                cliente=cliente,
                valor_base=plano.valor_base,
                valor_multa_juros=Decimal('0.00'),
                valor_total_devido=plano.valor_base,
                data_vencimento=data_vencimento,
                referencia_ciclo=data_vencimento.strftime("%Y-%m"),
                status_cobranca='PENDENTE'
            )
            self.stdout.write(self.style.SUCCESS(f'Cobrança criada: {cobranca}'))
        return cobranca
    
    def _test_email_sending(self, cobranca: Cobranca) -> None:
        """Test email sending."""
        self.stdout.write(self.style.WARNING('\nTentando enviar e-mail...'))
        self.stdout.write(f'Destinatário: {cobranca.cliente.email}')
        self.stdout.write(f'Assunto: Pilates - Aviso de Cobrança: Lembrete (D-3)')
        
        try:
            sucesso, detalhe = EmailService.send_billing_notification(
                cobranca,
                'Lembrete (D-3)'
            )
            
            if sucesso:
                self.stdout.write(self.style.SUCCESS(f'\n[OK] E-MAIL ENVIADO COM SUCESSO!'))
                self.stdout.write(self.style.SUCCESS(f'Detalhe: {detalhe}'))
                self.stdout.write(
                    self.style.SUCCESS(f'\nVerifique a caixa de entrada de: {cobranca.cliente.email}')
                )
            else:
                self.stdout.write(self.style.ERROR(f'\n[ERRO] FALHA NO ENVIO DE E-MAIL'))
                self.stdout.write(self.style.ERROR(f'Erro: {detalhe}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n[ERRO] ERRO AO TESTAR E-MAIL: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
