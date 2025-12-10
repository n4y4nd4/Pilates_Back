"""
Tests for service layer.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from cobranca_app.models import Plano, Cliente, Cobranca
from cobranca_app.services.servico_cobranca import ServicoCobranca
from cobranca_app.services.servico_cliente import ServicoCliente
from cobranca_app.core.excecoes import ExcecaoCliente
from cobranca_app.services.construtor_mensagem import ConstrutorMensagem
from cobranca_app.core.constantes import StatusCobranca, DIAS_ANTES_VENCIMENTO_LEMBRETE


class ServicoCobrancaTest(TestCase):
    """Tests for ServicoCobranca."""
    
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
            cpf="53372276079",
            telefone_whatsapp="5521999999999",
            email="teste@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
    
    def test_create_initial_billing(self):
        """Test initial billing creation."""
        cobranca = ServicoCobranca.criar_cobranca_inicial(self.cliente)
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
        count = ServicoCobranca.marcar_cobrancas_atrasadas()
        self.assertEqual(count, 1)
        cobranca.refresh_from_db()
        self.assertTrue(cobranca.is_atrasado())
    
    def test_get_billings_for_reminder(self):
        """Test getting billings for reminder."""
        reminder_date = timezone.localdate() + timedelta(days=DIAS_ANTES_VENCIMENTO_LEMBRETE)
        cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=reminder_date,
            referencia_ciclo="2025-12",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
        billings = ServicoCobranca.obter_cobrancas_para_lembrete(reminder_date)
        self.assertEqual(len(billings), 1)
        self.assertEqual(billings[0], cobranca)


class ServicoClienteTest(TestCase):
    """Tests for ServicoCliente."""
    
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
            cpf="94200547400",
            telefone_whatsapp="5521999887766",
            email="novo@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        ServicoCliente.criar_cliente_com_cobranca_inicial(cliente)
        
        # Refresh from DB to get ID
        cliente.refresh_from_db()
        self.assertIsNotNone(cliente.pk)
        cobranca = cliente.get_ultima_cobranca()
        self.assertIsNotNone(cobranca)


class ConstrutorMensagemTest(TestCase):
    """Tests for ConstrutorMensagem."""
    
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
            cpf="53372276079",
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
        tipo_regua, conteudo = ConstrutorMensagem.construir_mensagem_lembrete(self.cobranca)
        self.assertEqual(tipo_regua, 'Lembrete (D-3)')
        self.assertIn("Cliente Teste", conteudo)
        self.assertIn("150.00", conteudo)
    
    def test_build_overdue_message_d1(self):
        """Test overdue message for D+1."""
        from cobranca_app.core.constantes import DIAS_APOS_VENCIMENTO_AVISO_1
        tipo_regua, conteudo = ConstrutorMensagem.construir_mensagem_atraso(self.cobranca, DIAS_APOS_VENCIMENTO_AVISO_1)
        self.assertEqual(tipo_regua, 'Atraso (D+1)')
        self.assertIn("ATRASO", conteudo)
    
    def test_build_overdue_message_d10(self):
        """Test overdue message for D+10."""
        from cobranca_app.core.constantes import DIAS_APOS_VENCIMENTO_AVISO_2
        tipo_regua, conteudo = ConstrutorMensagem.construir_mensagem_atraso(self.cobranca, DIAS_APOS_VENCIMENTO_AVISO_2)
        self.assertEqual(tipo_regua, 'Aviso de Bloqueio (D+10)')
        self.assertIn("ATRASO", conteudo)

