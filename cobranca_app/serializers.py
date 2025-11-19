"""
DRF Serializers for API serialization/deserialization.
Following Clean Code: clear field definitions and validation.
"""
from rest_framework import serializers
from cobranca_app.models import Plano, Cliente, Cobranca


class PlanoSerializer(serializers.ModelSerializer):
    """Serializer for service plans (read-only)."""
    
    class Meta:
        model = Plano
        fields = '__all__'
        read_only_fields = '__all__'


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer for client operations (create, read, update, delete)."""
    
    plano_nome = serializers.ReadOnlyField(
        source='plano.nome_plano',
        help_text="Nome do plano associado ao cliente"
    )
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ('status_cliente',)
        
    def validate_plano(self, value):
        """Validate that the plan is active."""
        if value and not value.ativo:
            raise serializers.ValidationError("O plano selecionado não está ativo.")
        return value


class CobrancaSerializer(serializers.ModelSerializer):
    """Serializer for billing operations."""
    
    cliente_nome = serializers.ReadOnlyField(
        source='cliente.nome',
        help_text="Nome do cliente associado à cobrança"
    )
    
    class Meta:
        model = Cobranca
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'valor_total_devido',
            'data_vencimento',
            'status_cobranca',
            'data_pagamento'
        ]
        read_only_fields = ('cliente', 'cliente_nome', 'valor_total_devido',)
