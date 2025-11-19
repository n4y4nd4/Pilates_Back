"""
Tests for models and their business logic methods.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from cobranca_app.models import Plano, Cliente, Cobranca, Notificacao
from cobranca_app.core.constants import (
    StatusCliente,
    StatusCobranca,
    StatusEnvio
)


class PlanoModelTest(TestCase):
    """Tests for Plano model."""
    
    def setUp(self):
        """Set up test data."""
        self.plano = Plano.objects.create(
            nome_plano="Plano Mensal",
            valor_base=Decimal('150.00'),
            periodicidade_meses=1,
            ativo=True
        )
    
    def test_plano_str(self):
        """Test Plano string representation."""
        self.assertEqual(str(self.plano), "Plano Mensal")
    
    def test_calcular_valor_total(self):
        """Test total value calculation."""
        multa = Decimal('10.00')
        total = self.plano.calcular_valor_total(multa)
        self.assertEqual(total, Decimal('160.00'))


class ClienteModelTest(TestCase):
    """Tests for Cliente model."""
    
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
            status_cliente=StatusCliente.ATIVO.value
        )
    
    def test_cliente_str(self):
        """Test Cliente string representation."""
        self.assertEqual(str(self.cliente), "Cliente Teste")
    
    def test_is_ativo(self):
        """Test active status check."""
        self.assertTrue(self.cliente.is_ativo())
        self.cliente.status_cliente = StatusCliente.INATIVO_ATRASO.value
        self.assertFalse(self.cliente.is_ativo())
    
    def test_calcular_proxima_data_vencimento(self):
        """Test due date calculation."""
        due_date = self.cliente.calcular_proxima_data_vencimento()
        # Should be in the future
        self.assertGreaterEqual(due_date, timezone.localdate())
    
    def test_get_ultima_cobranca(self):
        """Test getting last billing."""
        cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=timezone.localdate() + timedelta(days=30),
            referencia_ciclo="2025-12",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
        ultima = self.cliente.get_ultima_cobranca()
        self.assertEqual(ultima, cobranca)


class CobrancaModelTest(TestCase):
    """Tests for Cobranca model."""
    
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
            status_cliente=StatusCliente.ATIVO.value
        )
        self.cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=timezone.localdate() + timedelta(days=30),
            referencia_ciclo="2025-12",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
    
    def test_cobranca_str(self):
        """Test Cobranca string representation."""
        self.assertIn("2025-12", str(self.cobranca))
        self.assertIn("Cliente Teste", str(self.cobranca))
    
    def test_status_checks(self):
        """Test status check methods."""
        self.assertTrue(self.cobranca.is_pendente())
        self.assertFalse(self.cobranca.is_pago())
        self.assertFalse(self.cobranca.is_atrasado())
    
    def test_is_vencida(self):
        """Test overdue check."""
        self.cobranca.data_vencimento = timezone.localdate() - timedelta(days=1)
        self.assertTrue(self.cobranca.is_vencida())
    
    def test_calcular_dias_atraso(self):
        """Test days overdue calculation."""
        self.cobranca.data_vencimento = timezone.localdate() - timedelta(days=5)
        self.cobranca.status_cobranca = StatusCobranca.ATRASADO.value
        dias = self.cobranca.calcular_dias_atraso()
        self.assertEqual(dias, 5)
    
    def test_marcar_como_pago(self):
        """Test marking as paid."""
        self.cobranca.marcar_como_pago()
        self.assertTrue(self.cobranca.is_pago())
        self.assertIsNotNone(self.cobranca.data_pagamento)
        self.assertEqual(self.cobranca.valor_multa_juros, Decimal('0.00'))
    
    def test_marcar_como_atrasado(self):
        """Test marking as overdue."""
        self.cobranca.marcar_como_atrasado()
        self.assertTrue(self.cobranca.is_atrasado())


class NotificacaoModelTest(TestCase):
    """Tests for Notificacao model."""
    
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
            status_cliente=StatusCliente.ATIVO.value
        )
        self.cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=timezone.localdate() + timedelta(days=30),
            referencia_ciclo="2025-12",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
        self.notificacao = Notificacao.objects.create(
            cobranca=self.cobranca,
            tipo_regua="Lembrete (D-3)",
            tipo_canal="Email",
            conteudo_mensagem="Teste",
            data_agendada=timezone.now(),
            status_envio=StatusEnvio.AGENDADO.value
        )
    
    def test_notificacao_str(self):
        """Test Notificacao string representation."""
        self.assertIn("Cliente Teste", str(self.notificacao))
        self.assertIn("Email", str(self.notificacao))
    
    def test_marcar_como_enviada(self):
        """Test marking as sent."""
        self.notificacao.marcar_como_enviada()
        self.assertEqual(self.notificacao.status_envio, StatusEnvio.ENVIADO.value)
        self.assertIsNotNone(self.notificacao.data_envio_real)
    
    def test_marcar_como_falha(self):
        """Test marking as failed."""
        self.notificacao.marcar_como_falha()
        self.assertEqual(self.notificacao.status_envio, StatusEnvio.FALHA.value)
        self.assertIsNotNone(self.notificacao.data_envio_real)

