from django.db import models

class Plano(models.Model):
    nome_plano = models.CharField(max_length=100)
    valor_base = models.DecimalField(max_digits=10, decimal_places=2)
    periodicidade_meses = models.IntegerField(default=1)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome_plano
    
    class Meta:
        verbose_name = "Plano de Serviço"
        verbose_name_plural = "Planos de Serviço"



STATUS_CLIENTE_CHOICES = [
    ('ATIVO', 'Ativo'),
    ('INATIVO_ATRASO', 'Inativo por Atraso'), 
    ('INATIVO_MANUAL', 'Inativo Manual'),
]

class Cliente(models.Model):
    plano = models.ForeignKey('Plano', on_delete=models.SET_NULL, null=True, blank=True)
    
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    telefone_whatsapp = models.CharField(max_length=15)
    email = models.EmailField()
    
    data_inicio_contrato = models.DateField()
    
    status_cliente = models.CharField(
        max_length=20,
        choices=STATUS_CLIENTE_CHOICES,
        default='ATIVO'
    )
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

STATUS_COBRANCA_CHOICES = [
    ('PENDENTE', 'Pendente'),
    ('PAGO', 'Pago'),
    ('ATRASADO', 'Atrasado'),
    ('CANCELADO', 'Cancelado'),
]

class Cobranca(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    
    valor_base = models.DecimalField(max_digits=10, decimal_places=2)
    valor_multa_juros = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_total_devido = models.DecimalField(max_digits=10, decimal_places=2) # Base + Multa
    
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    referencia_ciclo = models.CharField(max_length=7) 
    
    status_cobranca = models.CharField(
        max_length=10,
        choices=STATUS_COBRANCA_CHOICES,
        default='PENDENTE'
    )
    
    def __str__(self):
        return f"Cobrança {self.referencia_ciclo} - {self.cliente.nome}"
    
    class Meta:
        verbose_name = "Cobrança"
        verbose_name_plural = "Cobranças"
        ordering = ['-data_vencimento'] 


STATUS_ENVIO_CHOICES = [
    ('AGENDADO', 'Agendado'),
    ('ENVIADO', 'Enviado'),
    ('FALHA', 'Falha'),
]

class Notificacao(models.Model):
    cobranca = models.ForeignKey('Cobranca', on_delete=models.CASCADE)
    
    tipo_regua = models.CharField(max_length=50) 
    tipo_canal = models.CharField(max_length=10) 
    conteudo_mensagem = models.TextField() 
    
    data_agendada = models.DateTimeField()
    data_envio_real = models.DateTimeField(null=True, blank=True)
    
    status_envio = models.CharField(
        max_length=10,
        choices=STATUS_ENVIO_CHOICES,
        default='AGENDADO'
    )

    def __str__(self):
        return f"Notificação para {self.cobranca.cliente.nome} ({self.tipo_canal})"
    
    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-data_agendada'] 
        
