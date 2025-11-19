"""
Tests for service layer.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from cobranca_app.models import Plano, Cliente, Cobranca
from cobranca_app.services.billing_service import BillingService
from cobranca_app.services.cliente_service import ClienteService
from cobranca_app.core.exceptions import ClienteException
from cobranca_app.services.message_builder import MessageBuilder
from cobranca_app.core.constants import StatusCobranca, DAYS_BEFORE_DUE_REMINDER


class BillingServiceTest(TestCase):
    """Tests for BillingService."""
    
    def setUp(self):
        """Set up test data."""
        self.plano = Plano.objects.create(
            nome_plano="Plano Mensal",
            valor_base=Decimal('150.00'),
            periodicidade_meses=1,
            ativo=True
        )
        self.cliente = Cliente.objects.create(
            plano=self.plano,
            nome="Cliente Teste",
            cpf="12345678901",
            telefone_whatsapp="5521999999999",
            email="teste@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
    
    def test_create_initial_billing(self):
        """Test initial billing creation."""
        cobranca = BillingService.create_initial_billing(self.cliente)
        self.assertIsNotNone(cobranca)
        self.assertEqual(cobranca.cliente, self.cliente)
        self.assertEqual(cobranca.valor_base, Decimal('150.00'))
        self.assertEqual(cobranca.status_cobranca, StatusCobranca.PENDENTE.value)
    
    def test_mark_overdue_billings(self):
        """Test marking overdue billings."""
        cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=timezone.localdate() - timedelta(days=1),
            referencia_ciclo="2025-11",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
        count = BillingService.mark_overdue_billings()
        self.assertEqual(count, 1)
        cobranca.refresh_from_db()
        self.assertTrue(cobranca.is_atrasado())
    
    def test_get_billings_for_reminder(self):
        """Test getting billings for reminder."""
        reminder_date = timezone.localdate() + timedelta(days=DAYS_BEFORE_DUE_REMINDER)
        cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=reminder_date,
            referencia_ciclo="2025-12",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
        billings = BillingService.get_billings_for_reminder(reminder_date)
        self.assertEqual(len(billings), 1)
        self.assertEqual(billings[0], cobranca)


class ClienteServiceTest(TestCase):
    """Tests for ClienteService."""
    
    def setUp(self):
        """Set up test data."""
        self.plano = Plano.objects.create(
            nome_plano="Plano Mensal",
            valor_base=Decimal('150.00'),
            periodicidade_meses=1,
            ativo=True
        )
    
    def test_create_client_with_initial_billing(self):
        """Test client creation with initial billing."""
        cliente = Cliente(
            plano=self.plano,
            nome="Novo Cliente",
            cpf="98765432100",
            telefone_whatsapp="5521999887766",
            email="novo@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        ClienteService.create_client_with_initial_billing(cliente)
        
        # Refresh from DB to get ID
        cliente.refresh_from_db()
        self.assertIsNotNone(cliente.id)
        cobranca = cliente.get_ultima_cobranca()
        self.assertIsNotNone(cobranca)


class MessageBuilderTest(TestCase):
    """Tests for MessageBuilder."""
    
    def setUp(self):
        """Set up test data."""
        self.plano = Plano.objects.create(
            nome_plano="Plano Mensal",
            valor_base=Decimal('150.00'),
            periodicidade_meses=1,
            ativo=True
        )
        self.cliente = Cliente.objects.create(
            plano=self.plano,
            nome="Cliente Teste",
            cpf="12345678901",
            telefone_whatsapp="5521999999999",
            email="teste@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        self.cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=timezone.localdate() + timedelta(days=3),
            referencia_ciclo="2025-12",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
    
    def test_build_reminder_message(self):
        """Test reminder message building."""
        tipo_regua, conteudo = MessageBuilder.build_reminder_message(self.cobranca)
        self.assertEqual(tipo_regua, 'Lembrete (D-3)')
        self.assertIn("Cliente Teste", conteudo)
        self.assertIn("150.00", conteudo)
    
    def test_build_overdue_message_d1(self):
        """Test overdue message for D+1."""
        from cobranca_app.core.constants import DAYS_AFTER_DUE_WARNING_1
        tipo_regua, conteudo = MessageBuilder.build_overdue_message(self.cobranca, DAYS_AFTER_DUE_WARNING_1)
        self.assertEqual(tipo_regua, 'Atraso (D+1)')
        self.assertIn("ATRASO", conteudo)
    
    def test_build_overdue_message_d10(self):
        """Test overdue message for D+10."""
        from cobranca_app.core.constants import DAYS_AFTER_DUE_WARNING_2
        tipo_regua, conteudo = MessageBuilder.build_overdue_message(self.cobranca, DAYS_AFTER_DUE_WARNING_2)
        self.assertEqual(tipo_regua, 'Aviso de Bloqueio (D+10)')
        self.assertIn("ATRASO", conteudo)

