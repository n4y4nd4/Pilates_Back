"""
Tests for API endpoints.
"""
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from cobranca_app.models import Plano, Cliente, Cobranca
from cobranca_app.core.constantes import StatusCobranca


class ClienteAPITest(TransactionTestCase):
    """Tests for Cliente API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.plano = Plano.objects.create(
            nome_plano="Plano Mensal",
            valor_base=Decimal('150.00'),
            periodicidade_meses=1,
            ativo=True
        )
    
    def test_list_clientes(self):
        """Test listing clients."""
        Cliente.objects.create(
            plano=self.plano,
            nome="Cliente 1",
            cpf="85202874015",
            telefone_whatsapp="5521999999999",
            email="cliente1@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        
        url = reverse('cliente-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_cliente(self):
        """Test creating a client."""
        url = reverse('cliente-list')
        data = {
            'plano': self.plano.pk,
            'nome': 'Novo Cliente',
            'cpf': '111.444.777-35',
            'telefone_whatsapp': '5521999887766',
            'email': 'novo@example.com',
            'data_inicio_contrato': '2025-01-20'
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Validation Error: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify client was created
        cliente = Cliente.objects.get(cpf='11144477735')
        self.assertEqual(cliente.nome, 'Novo Cliente')
        
        # Verify initial billing was created
        cobranca = cliente.get_ultima_cobranca()
        self.assertIsNotNone(cobranca)
    
    def test_get_cliente_detail(self):
        """Test getting client details."""
        cliente = Cliente.objects.create(
            plano=self.plano,
            nome="Cliente Teste",
            cpf="66128841003",
            telefone_whatsapp="5521999776655",
            email="teste@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        
        url = reverse('cliente-detail', kwargs={'pk': cliente.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Cliente Teste')
    
    def test_update_cliente(self):
        """Test updating a client."""
        cliente = Cliente.objects.create(
            plano=self.plano,
            nome="Cliente Original",
            cpf="94957245084",
            telefone_whatsapp="5521999665544",
            email="original@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        
        url = reverse('cliente-detail', kwargs={'pk': cliente.pk})
        data = {'nome': 'Cliente Atualizado'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        cliente.refresh_from_db()
        self.assertEqual(cliente.nome, 'Cliente Atualizado')
    
    def test_delete_cliente(self):
        """Test deleting a client."""
        cliente = Cliente.objects.create(
            plano=self.plano,
            nome="Cliente Para Deletar",
            cpf="63935686001",
            telefone_whatsapp="5521999554433",
            email="deletar@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        
        url = reverse('cliente-detail', kwargs={'pk': cliente.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cliente.objects.filter(pk=cliente.pk).exists())

    def tearDown(self):
        """Clean up after each test."""
        Cobranca.objects.all().delete()
        Cliente.objects.all().delete()
        Plano.objects.all().delete()


class CobrancaAPITest(TransactionTestCase):
    """Tests for Cobranca API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.plano = Plano.objects.create(
            nome_plano="Plano Mensal",
            valor_base=Decimal('150.00'),
            periodicidade_meses=1,
            ativo=True
        )
        self.cliente = Cliente.objects.create(
            plano=self.plano,
            nome="Cliente Teste",
            cpf="47656627061",
            telefone_whatsapp="5521999443322",
            email="teste@example.com",
            data_inicio_contrato=timezone.localdate(),
            status_cliente='ATIVO'
        )
        self.cobranca = Cobranca.objects.create(
            cliente=self.cliente,
            valor_base=Decimal('150.00'),
            valor_total_devido=Decimal('150.00'),
            data_vencimento=timezone.localdate() + timedelta(days=30),
            referencia_ciclo="2025-12",
            status_cobranca=StatusCobranca.PENDENTE.value
        )
    
    def tearDown(self):
        """Clean up after each test."""
        Cobranca.objects.all().delete()
        Cliente.objects.all().delete()
        Plano.objects.all().delete()
    
    def test_list_cobrancas(self):
        """Test listing billings."""
        url = reverse('cobranca-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_get_cobranca_detail(self):
        """Test getting billing details."""
        url = reverse('cobranca-detail', kwargs={'pk': self.cobranca.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.cobranca.pk)
    
    def test_marcar_pago(self):
        """Test marking billing as paid."""
        url = reverse('cobranca-marcar-pago', kwargs={'pk': self.cobranca.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.cobranca.refresh_from_db()
        self.assertTrue(self.cobranca.is_pago())
        self.assertIsNotNone(self.cobranca.data_pagamento)
    
    def test_marcar_pago_already_paid(self):
        """Test marking already paid billing."""
        self.cobranca.marcar_como_pago()
        
        url = reverse('cobranca-marcar-pago', kwargs={'pk': self.cobranca.pk})
        response = self.client.patch(url)
        # Should still return 200, but billing is already paid
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PlanoAPITest(TransactionTestCase):
    """Tests for Plano API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.plano = Plano.objects.create(
            nome_plano="Plano Mensal",
            valor_base=Decimal('150.00'),
            periodicidade_meses=1,
            ativo=True
        )
    
    def test_list_planos(self):
        """Test listing plans."""
        url = reverse('plano-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nome_plano'], 'Plano Mensal')
    
    def test_list_only_active_planos(self):
        """Test that only active plans are listed."""
        Plano.objects.create(
            nome_plano="Plano Inativo",
            valor_base=Decimal('100.00'),
            periodicidade_meses=1,
            ativo=False
        )
        
        url = reverse('plano-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return active plan
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nome_plano'], 'Plano Mensal')

    def tearDown(self):
        """Clean up after each test."""
        Cobranca.objects.all().delete()
        Cliente.objects.all().delete()
        Plano.objects.all().delete()

