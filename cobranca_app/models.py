"""
Django models for the billing application.
Following Clean Code: models contain business logic methods.
"""
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from cobranca_app.core.constantes import (
    StatusCliente,
    StatusCobranca,
    StatusEnvio,
    TipoCanal,
    DIAS_POR_MES,
    FORMATO_DATA_REFERENCIA
)
from cobranca_app.core.utilitarios import calcular_data_vencimento


class Plano(models.Model):
    """Service plan model."""
    
    nome_plano = models.CharField(max_length=100, verbose_name="Nome do Plano")
    valor_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Base"
    )
    periodicidade_meses = models.IntegerField(
        default=1,
        verbose_name="Periodicidade (meses)"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    def __str__(self) -> str:
        return self.nome_plano
    
    def calcular_valor_total(self, multa_juros: Decimal = Decimal('0.00')) -> Decimal:
        """
        Calculate total amount including fees.
        
        Args:
            multa_juros: Additional fees amount
        
        Returns:
            Total amount due
        """
        return self.valor_base + multa_juros
    
    class Meta:
        verbose_name = "Plano de Serviço"
        verbose_name_plural = "Planos de Serviço"
        ordering = ['nome_plano']


class Cliente(models.Model):
    """Client model."""
    
    STATUS_CHOICES = [
        (StatusCliente.ATIVO.value, 'Ativo'),
        (StatusCliente.INATIVO_ATRASO.value, 'Inativo por Atraso'),
        (StatusCliente.INATIVO_MANUAL.value, 'Inativo Manual'),
]

    plano = models.ForeignKey(
        'Plano',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Plano"
    )
    nome = models.CharField(max_length=200, verbose_name="Nome")
    cpf = models.CharField(
        max_length=14,
        unique=True,
        primary_key=True,
        verbose_name="CPF",
        help_text="CPF do cliente (pode incluir pontos e traço)"
    )
    telefone_whatsapp = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Telefone WhatsApp",
        help_text="Telefone no formato: código do país + DDD + número"
    )
    email = models.EmailField(
        unique=True,
        verbose_name="E-mail",
        help_text="E-mail único do cliente"
    )
    data_inicio_contrato = models.DateField(verbose_name="Data de Início do Contrato")
    status_cliente = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=StatusCliente.ATIVO.value,
        verbose_name="Status do Cliente"
    )
    
    def __str__(self) -> str:
        return self.nome
    
    def is_ativo(self) -> bool:
        """Check if client is active."""
        return self.status_cliente == StatusCliente.ATIVO.value
    
    def calcular_proxima_data_vencimento(self) -> date:
        """
        Calculate next due date based on contract start and plan periodicity.
        
        Returns:
            Next due date
        """
        if not self.plano:
            raise ValueError("Cliente must have a plan to calculate due date")
        
        return calcular_data_vencimento(
            data_inicio=self.data_inicio_contrato,
            periodicidade_meses=self.plano.periodicidade_meses
        )
    
    def get_ultima_cobranca(self) -> Optional['Cobranca']:
        """
        Get the most recent billing for this client.
        
        Returns:
            Most recent Cobranca or None
        """
        return self.cobranca_set.order_by('-data_vencimento').first()
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']


class Cobranca(models.Model):
    """Billing model."""
    
    STATUS_CHOICES = [
        (StatusCobranca.PENDENTE.value, 'Pendente'),
        (StatusCobranca.PAGO.value, 'Pago'),
        (StatusCobranca.ATRASADO.value, 'Atrasado'),
        (StatusCobranca.CANCELADO.value, 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        verbose_name="Cliente"
    )
    valor_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Base"
    )
    valor_multa_juros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Multa e Juros"
    )
    valor_total_devido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Total Devido"
    )
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Pagamento"
    )
    referencia_ciclo = models.CharField(
        max_length=7,
        verbose_name="Referência do Ciclo"
    )
    status_cobranca = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=StatusCobranca.PENDENTE.value,
        verbose_name="Status da Cobrança"
    )
    
    def __str__(self) -> str:
        return f"Cobrança {self.referencia_ciclo} - {self.cliente.nome}"
    
    def is_pendente(self) -> bool:
        """Check if billing is pending."""
        return self.status_cobranca == StatusCobranca.PENDENTE.value
    
    def is_pago(self) -> bool:
        """Check if billing is paid."""
        return self.status_cobranca == StatusCobranca.PAGO.value
    
    def is_atrasado(self) -> bool:
        """Check if billing is overdue."""
        return self.status_cobranca == StatusCobranca.ATRASADO.value
    
    def is_vencida(self) -> bool:
        """
        Check if billing is past due date.
        
        Returns:
            True if due date has passed and status is not paid
        """
        hoje = timezone.localdate()
        return self.data_vencimento < hoje and not self.is_pago()
    
    def calcular_dias_atraso(self) -> int:
        """
        Calculate days overdue.
        
        Returns:
            Number of days overdue, or 0 if not overdue
        """
        if not self.is_vencida():
            return 0
        hoje = timezone.localdate()
        return (hoje - self.data_vencimento).days
    
    def marcar_como_pago(self) -> None:
        """Mark billing as paid."""
        self.status_cobranca = StatusCobranca.PAGO.value
        self.data_pagamento = timezone.localdate()
        self.valor_multa_juros = Decimal('0.00')
        self.save()
    
    def marcar_como_atrasado(self) -> None:
        """Mark billing as overdue."""
        if self.is_pendente():
            self.status_cobranca = StatusCobranca.ATRASADO.value
            self.save()
    
    class Meta:
        verbose_name = "Cobrança"
        verbose_name_plural = "Cobranças"
        ordering = ['-data_vencimento'] 


class Notificacao(models.Model):
    """Notification model."""
    
    STATUS_CHOICES = [
        (StatusEnvio.AGENDADO.value, 'Agendado'),
        (StatusEnvio.ENVIADO.value, 'Enviado'),
        (StatusEnvio.FALHA.value, 'Falha'),
]

    cobranca = models.ForeignKey(
        'Cobranca',
        on_delete=models.CASCADE,
        verbose_name="Cobrança"
    )
    tipo_regua = models.CharField(
        max_length=50,
        verbose_name="Tipo de Régua"
    )
    tipo_canal = models.CharField(
        max_length=10,
        verbose_name="Tipo de Canal"
    )
    conteudo_mensagem = models.TextField(verbose_name="Conteúdo da Mensagem")
    data_agendada = models.DateTimeField(verbose_name="Data Agendada")
    data_envio_real = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Envio Real"
    )
    status_envio = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=StatusEnvio.AGENDADO.value,
        verbose_name="Status de Envio"
    )

    def __str__(self) -> str:
        return f"Notificação para {self.cobranca.cliente.nome} ({self.tipo_canal})"
    
    def marcar_como_enviada(self) -> None:
        """Mark notification as sent."""
        self.status_envio = StatusEnvio.ENVIADO.value
        self.data_envio_real = timezone.now()
        self.save()
    
    def marcar_como_falha(self) -> None:
        """Mark notification as failed."""
        self.status_envio = StatusEnvio.FALHA.value
        self.data_envio_real = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-data_agendada'] 
