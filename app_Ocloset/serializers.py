from datetime import timedelta
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from django.utils import timezone

from .models import (
    Usuarios, Roupas, RoupasImagens,
    Reservas, Alugueis, Pagamentos
)

class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Usuarios.
    Ele vai automaticamente incluir todos os campos do modelo.
    """
    class Meta:
        model = Usuarios
        fields = '__all__'

class RoupaImagemSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo RoupasImagens.
    Usado para adicionar/remover imagens e para 
    mostrar as imagens dentro de uma Roupa.
    """
    class Meta:
        model = RoupasImagens
        fields = ['id', 'roupa', 'url', 'criado_em']
        read_only_fields = ['criado_em']


class RoupaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Roupas.
    AGORA VAI INCLUIR AS IMAGENS
    """
    usuario = serializers.StringRelatedField(read_only=True)
    
    imagens = RoupaImagemSerializer(
        many=True,      
        read_only=True, 
        source='roupasimagens_set' 
    )

    class Meta:
        model = Roupas
        fields = [
            'id', 
            'usuario', 
            'marca', 'cor', 'tamanho', 'descricao', 
            'cuidados', 'ocasiao', 'valor', 'status', 'criado_em', 
            'atualizado_em', 
            'imagens' 
        ]
        
class CadastroSerializer(serializers.ModelSerializer):
    """
    Serializer para criar um novo Utilizador (User) e
    o perfil de Usuário (Usuarios) ao mesmo tempo.
    """
    
    password = serializers.CharField(
        write_only=True, 
        required=True,
        validators=[validate_password] 
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label="Confirmação de password"
    )

    class Meta:
        model = Usuarios
        fields = ['email', 'nome', 'cpf', 'telefone', 'cidade', 'bairro', 'endereco','password', 'password2']
    
    def validate(self, attrs):
        """
        Verifica se as duas passwords são iguais.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords não são iguais."})
        
        if User.objects.filter(username=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Este email já está em uso."})

        if Usuarios.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Este email já está em uso."})

        return attrs

    def create(self, validated_data):
        """
        Cria os dois objetos (User e Usuarios) numa transação.
        """
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=validated_data['email'],
                    email=validated_data['email'],
                    password=validated_data['password']
                )

                validated_data.pop('password')
                validated_data.pop('password2')

                usuario_perfil = Usuarios.objects.create(
                    user=user, 
                    **validated_data
                )
                
                return usuario_perfil

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
class ReservaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Reservas.
    """
    
    usuario = serializers.StringRelatedField(read_only=True)
    
    status = serializers.CharField(read_only=True)
    criado_em = serializers.DateTimeField(read_only=True)
    
    
    class Meta:
        model = Reservas
        fields = [
            'id', 'usuario', 'roupa', 'data_inicio', 'data_fim', 
            'status', 'criado_em'
        ]

    def validate(self, data):
        """
        Validação personalizada para as datas.
        """
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        
        if data_inicio <= timezone.now().date():
            raise serializers.ValidationError(
                "A data de início da reserva deve ser no futuro."
            )
            
        if data_fim <= data_inicio:
            raise serializers.ValidationError(
                "A data de fim deve ser posterior à data de início."
            )
            
        return data
    

class AluguelSerializer(serializers.ModelSerializer):
    """
    Serializer para MOSTRAR o modelo Alugueis.
    (Este serializer agora é apenas para leitura/display)
    """
    usuario = serializers.StringRelatedField()
    roupa = serializers.StringRelatedField()
    reserva = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Alugueis
        fields = [
            'id', 'reserva', 'usuario', 'roupa', 'data_inicio', 
            'data_fim', 'status', 'criado_em'
        ]
        read_only_fields = fields 


class AluguelCreateSerializer(serializers.Serializer):
    """
    Serializer para CRIAR um novo Aluguel a partir de uma Reserva.
    Aceita o ID da reserva e o método de pagamento.
    """
    reserva = serializers.PrimaryKeyRelatedField(
        queryset=Reservas.objects.all(),
        label="ID da Reserva"
    )
    metodo = serializers.CharField(max_length=50, write_only=True)

    default_error_messages = {
        'dono_invalido': 'Você só pode alugar reservas que você mesmo criou.',
        'status_invalido': 'Esta reserva não está mais pendente.',
        'expirada': 'Esta reserva expirou (limite de 24h).',
        'sem_data': 'Falha interna: reserva sem data de criação.',
        'transacao_falhou': 'Falha ao processar o pagamento e aluguel.'
    }

    def validate(self, data):
        """
        Valida a reserva antes de tentar criar o aluguel.
        """
        reserva = data.get('reserva')
        
        try:
            usuario_perfil = self.context['request'].user.usuarios
        except Usuarios.DoesNotExist:
             raise serializers.ValidationError("Perfil de usuário não encontrado.")

        if reserva.usuario != usuario_perfil:
            raise serializers.ValidationError(self.default_error_messages['dono_invalido'])

        if reserva.status != 'pendente':
            raise serializers.ValidationError(self.default_error_messages['status_invalido'])
        
        if reserva.criado_em is None:
            raise serializers.ValidationError(self.default_error_messages['sem_data'])

        limite_tempo = reserva.criado_em + timedelta(hours=24)
        if timezone.now() > limite_tempo:
            reserva.status = 'expirada'
            reserva.save()
            raise serializers.ValidationError(self.default_error_messages['expirada'])
        
        return data

    def create(self, validated_data):
        """
        Cria o Pagamento e o Aluguel (operação atómica).
        """
        reserva = validated_data.get('reserva')
        metodo = validated_data.get('metodo')
        usuario_perfil = self.context['request'].user.usuarios
        valor_aluguel = reserva.roupa.valor

        try:
            with transaction.atomic():
                Pagamentos.objects.create(
                    reserva=reserva,
                    valor=valor_aluguel,
                    metodo=metodo,
                    status='concluido' 
                )

                aluguel = Alugueis.objects.create(
                    reserva=reserva,
                    usuario=usuario_perfil,
                    roupa=reserva.roupa,
                    data_inicio=reserva.data_inicio,
                    data_fim=reserva.data_fim,
                    status='confirmado',
                    criado_em=timezone.now(),
                    atualizado_em=timezone.now()
                )

                reserva.status = 'confirmada' 
                reserva.save()
            
            return aluguel 

        except Exception as e:
            raise serializers.ValidationError(f"{self.default_error_messages['transacao_falhou']} {str(e)}")