# cobranca_app/serializers.py

from rest_framework import serializers
from .models import Plano, Cliente, Cobranca

# 1. Serializer para o Plano (Apenas leitura)
class PlanoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plano
        fields = '__all__' # Inclui todos os campos do Plano

# 2. Serializer para o Cliente (Para o cadastro)
class ClienteSerializer(serializers.ModelSerializer):
    # Usaremos esta classe para Cadastrar e Listar Clientes
    
    # Adicionamos o nome do plano para ser mais fácil de ler no React
    plano_nome = serializers.ReadOnlyField(source='plano.nome_plano') 
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ('status_cliente',) # O status não é alterado pelo usuário na criação
        
# 3. Serializer para a Cobrança (Para listagem e marcação de pagamento)
class CobrancaSerializer(serializers.ModelSerializer):
    # Puxa o nome do cliente para a listagem
    cliente_nome = serializers.ReadOnlyField(source='cliente.nome')
    
    class Meta:
        model = Cobranca
        # Incluímos apenas os campos que o React precisa
        fields = ['id', 'cliente', 'cliente_nome', 'valor_total_devido', 'data_vencimento', 'status_cobranca', 'data_pagamento']
        read_only_fields = ('cliente', 'cliente_nome', 'valor_total_devido',) # Campos que só o backend calcula