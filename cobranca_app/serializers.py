"""
DRF Serializers for API serialization/deserialization.
Following Clean Code: clear field definitions and validation.
"""
from rest_framework import serializers
from cobranca_app.models import Plano, Cliente, Cobranca, Notificacao


class PlanoSerializer(serializers.ModelSerializer):
    """Serializer for service plans (read-only)."""
    
    class Meta:
        model = Plano
        fields = '__all__'
        read_only_fields = ['id', 'nome_plano', 'valor_base', 'periodicidade_meses', 'ativo']


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer for client operations (create, read, update, delete)."""
    
    # Campo id que retorna o CPF para compatibilidade com frontend
    id = serializers.CharField(
        source='cpf',
        read_only=True,
        help_text="ID do cliente (CPF)"
    )
    
    plano_nome = serializers.ReadOnlyField(
        source='plano.nome_plano',
        help_text="Nome do plano associado ao cliente"
    )
    
    # Sobrescreve o campo email para usar CharField e ter controle total sobre validação
    email = serializers.CharField(
        max_length=254,
        help_text="E-mail único do cliente"
    )
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ('id', 'cpf')  # CPF é primary key, não pode ser atualizado
        # status_cliente foi removido de read_only_fields para permitir atualização manual
        extra_kwargs = {
            'cpf': {
                'validators': [],  # Remove validators padrão, usamos validação customizada
                'read_only': True,  # CPF não pode ser alterado após criação
            },
            'telefone_whatsapp': {
                'validators': [],  # Remove validators padrão, usamos validação customizada
            },
        }
    
    def validate_cpf(self, value):
        """
        Valida e normaliza o CPF.
        Durante updates, o CPF é read-only e não deve ser validado.
        
        Args:
            value: CPF a validar
        
        Returns:
            CPF normalizado (apenas dígitos)
        """
        # Se estiver atualizando (instance existe), o CPF não deve ser alterado
        if self.instance:
            # Retorna o CPF atual sem validar (já que é read-only)
            return self.instance.cpf
        
        from rest_framework import serializers as drf_serializers
        from cobranca_app.core.validadores import validar_cpf, validar_cpf_unico
        from cobranca_app.core.excecoes import ExcecaoDadosInvalidos
        
        try:
            # Valida formato e dígitos verificadores apenas na criação
            cpf_normalizado = validar_cpf(value)
            
            # Valida unicidade
            validar_cpf_unico(cpf_normalizado, None)
            
            return cpf_normalizado
        except ExcecaoDadosInvalidos as e:
            raise drf_serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        """
        Valida formato e unicidade do e-mail.
        
        Args:
            value: E-mail a validar
        
        Returns:
            E-mail validado
        """
        from rest_framework import serializers as drf_serializers
        from cobranca_app.core.validadores import validar_email_unico
        from cobranca_app.core.excecoes import ExcecaoDadosInvalidos
        import re
        
        if not value:
            raise drf_serializers.ValidationError("E-mail é obrigatório")
        
        # Valida formato básico de e-mail
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise drf_serializers.ValidationError("Formato de e-mail inválido. Use o formato: exemplo@dominio.com")
        
        try:
            # Valida unicidade (se estiver atualizando, passa o CPF atual)
            cliente_cpf = getattr(self.instance, 'cpf', None) if self.instance else None
            # Chama apenas a validação de unicidade (formato já foi validado acima)
            from cobranca_app.models import Cliente
            
            query = Cliente.objects.filter(email__iexact=value)
            if cliente_cpf:
                query = query.exclude(cpf=cliente_cpf)
            
            if query.exists():
                raise drf_serializers.ValidationError("Este e-mail já está cadastrado para outro cliente")
            
            return value
        except drf_serializers.ValidationError:
            raise
        except ExcecaoDadosInvalidos as e:
            raise drf_serializers.ValidationError(str(e))
    
    def validate_telefone_whatsapp(self, value):
        """
        Valida se o telefone é único.
        
        Args:
            value: Telefone a validar
        
        Returns:
            Telefone validado
        """
        from rest_framework import serializers as drf_serializers
        from cobranca_app.core.validadores import validar_telefone_unico
        from cobranca_app.core.excecoes import ExcecaoDadosInvalidos
        
        try:
            # Valida unicidade (se estiver atualizando, passa o CPF atual)
            cliente_cpf = getattr(self.instance, 'cpf', None) if self.instance else None
            validar_telefone_unico(value, cliente_cpf)
            return value
        except ExcecaoDadosInvalidos as e:
            raise drf_serializers.ValidationError(str(e))
        
    def validate_plano(self, value):
        """Validate that the plan is active."""
        if value and not value.ativo:
            raise serializers.ValidationError("O plano selecionado não está ativo.")
        return value
    
    def validate_status_cliente(self, value):
        """
        Valida que o status_cliente é um valor válido.
        
        Args:
            value: Status a validar
        
        Returns:
            Status validado
        """
        from cobranca_app.core.constantes import StatusCliente
        
        valores_validos = [StatusCliente.ATIVO.value, StatusCliente.INATIVO_ATRASO.value, StatusCliente.INATIVO_MANUAL.value]
        
        if value not in valores_validos:
            raise serializers.ValidationError(
                f"Valor inválido para status_cliente. Valores aceitos: {', '.join(valores_validos)}"
            )
        
        return value


class CobrancaSerializer(serializers.ModelSerializer):
    """Serializer for billing operations."""
    
    # Campo cliente retorna o CPF do cliente (não o ID)
    cliente = serializers.CharField(
        source='cliente.cpf',
        read_only=True,
        help_text="CPF do cliente associado à cobrança"
    )
    
    cliente_nome = serializers.ReadOnlyField(
        source='cliente.nome',
        help_text="Nome do cliente associado à cobrança"
    )
    
    cliente_cpf = serializers.ReadOnlyField(
        source='cliente.cpf',
        help_text="CPF do cliente associado à cobrança"
    )
    
    class Meta:
        model = Cobranca
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'cliente_cpf',
            'valor_base',
            'valor_multa_juros',
            'valor_total_devido',
            'data_vencimento',
            'data_pagamento',
            'referencia_ciclo',
            'status_cobranca',
        ]
        read_only_fields = (
            'cliente',
            'cliente_nome',
            'cliente_cpf',
            'valor_total_devido',
        )


class NotificacaoSerializer(serializers.ModelSerializer):
    """Serializer for notification operations."""
    
    cobranca_cliente_nome = serializers.SerializerMethodField(
        help_text="Nome do cliente associado à cobrança"
    )
    
    # Garantir que tipo_canal retorne em maiúsculas (EMAIL, WHATSAPP)
    tipo_canal = serializers.SerializerMethodField()
    
    # Permitir que conteudo_mensagem seja null/vazio
    conteudo_mensagem = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False
    )
    
    class Meta:
        model = Notificacao
        fields = [
            'id',
            'cobranca_cliente_nome',
            'data_envio_real',
            'data_agendada',
            'tipo_regua',
            'tipo_canal',
            'status_envio',
            'conteudo_mensagem',
        ]
        read_only_fields = ('cobranca_cliente_nome',)
    
    def get_cobranca_cliente_nome(self, obj):
        """
        Retorna o nome do cliente associado à cobrança.
        Retorna None se não houver cliente associado.
        """
        try:
            if obj.cobranca and obj.cobranca.cliente:
                return obj.cobranca.cliente.nome
        except AttributeError:
            pass
        return None
    
    def get_tipo_canal(self, obj):
        """
        Retorna o tipo de canal em maiúsculas para compatibilidade com o frontend.
        Converte 'Email' -> 'EMAIL' e 'WhatsApp' -> 'WHATSAPP'
        """
        canal = obj.tipo_canal.upper() if obj.tipo_canal else ''
        # Mapear variações possíveis
        if 'EMAIL' in canal:
            return 'EMAIL'
        elif 'WHATSAPP' in canal or 'WHATS' in canal:
            return 'WHATSAPP'
        return canal
