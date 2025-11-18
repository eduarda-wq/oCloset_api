from rest_framework import viewsets, generics, status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .permissions import IsRoupaOwnerOrReadOnly, IsRoupaImagemOwnerOrReadOnly
from .models import (
    Reservas, Usuarios, Roupas, RoupasImagens, Alugueis, Pagamentos
)
from .serializers import (
    AluguelCreateSerializer, UsuarioSerializer, RoupaSerializer, 
    RoupaImagemSerializer, CadastroSerializer,
    ReservaSerializer,
    AluguelSerializer
)
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound
from django.db.models import Q
from django.db import transaction
from rest_framework.decorators import action
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from rest_framework import mixins

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD de Usuários.
    Fornece automaticamente as ações:
    .list() - Listar todos (GET /api/usuarios/)
    .create() - Criar novo (POST /api/usuarios/)
    .retrieve() - Ver um específico (GET /api/usuarios/<id>/)
    .update() - Atualizar (PUT /api/usuarios/<id>/)
    .partial_update() - Atualizar parcialmente (PATCH /api/usuarios/<id>/)
    .destroy() - Apagar (DELETE /api/usuarios/<id>/)
    """
    queryset = Usuarios.objects.all() 
    
    serializer_class = UsuarioSerializer

class RoupaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD de Roupas.
    Funciona exatamente como o de Usuários, mas para o modelo Roupas.
    """
    queryset = Roupas.objects.all()
    serializer_class = RoupaSerializer
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsRoupaOwnerOrReadOnly]
    def perform_create(self, serializer):
        """
        Sobrescreve o método de criação.
        Associa automaticamente o 'Usuarios' perfil do utilizador logado.
        """
        try:
            usuario_perfil = Usuarios.objects.get(user=self.request.user)
        except Usuarios.DoesNotExist:
            raise ValidationError("Perfil de usuário não encontrado.")
            
        serializer.save(usuario=usuario_perfil)
    
class RoupaImagemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD das Imagens de Roupas.
    Permite Adicionar (POST) e Apagar (DELETE) imagens.
    """
    queryset = RoupasImagens.objects.all()
    serializer_class = RoupaImagemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsRoupaImagemOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        """
        Sobrescreve a criação para validar a posse da roupa
        antes de adicionar a imagem.
        """
        try:
            usuario_perfil = Usuarios.objects.get(user=self.request.user)
            
            roupa_alvo = serializer.validated_data.get('roupa')
            if roupa_alvo.usuario != usuario_perfil:
                raise ValidationError("Você só pode adicionar imagens às suas próprias roupas.")
                
        except Usuarios.DoesNotExist:
            raise ValidationError("Perfil de usuário não encontrado.")
            
        serializer.save()
    

class CadastroView(generics.CreateAPIView):
    """
    View para criar (cadastrar) um novo utilizador.
    Acessível publicamente (sem token).
    """
    queryset = Usuarios.objects.all()
    permission_classes = [AllowAny] 
    serializer_class = CadastroSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Utilizador criado com sucesso."}, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
class UserProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_object(self):
        """
        Sobrescreve a busca do objeto.
        Em vez de procurar por ID, retorna o perfil do utilizador do request.
        """
        try:
            return self.request.user.usuarios
        except AttributeError:
            raise NotFound("Perfil de utilizador não encontrado.")
        
class ReservaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para criar, ver e apagar Reservas.
    Um utilizador só pode ver/apagar as suas próprias reservas.
    """
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        """
        Filtra o queryset para retornar apenas
        as reservas do utilizador logado.
        """
        try:
            usuario_perfil = self.request.user.usuarios
            return Reservas.objects.filter(usuario=usuario_perfil)
        except Usuarios.DoesNotExist:
            return Reservas.objects.none()
    
    def perform_create(self, serializer):
        """
        Sobrescreve a criação para:
        1. Injetar o utilizador logado.
        2. Definir o status inicial como 'pendente'.
        3. Verificar colisão de datas (Requisito 2).
        """
        try:
            usuario_perfil = self.request.user.usuarios
        except Usuarios.DoesNotExist:
            raise ValidationError("Perfil de usuário não encontrado.")
            
        roupa = serializer.validated_data.get('roupa')
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        status_de_bloqueio = ['pendente', 'confirmada'] 

        conflitos = Reservas.objects.filter(
            roupa=roupa,
            status__in=status_de_bloqueio
        ).filter(
            Q(data_inicio__lte=data_fim) & Q(data_fim__gte=data_inicio)
        )

        if conflitos.exists():
            raise ValidationError(
                "Esta roupa já está reservada (ou pendente) para o período solicitado."
            )
        
        serializer.save(
            usuario=usuario_perfil,
            status='pendente',
            criado_em=timezone.now() 
        )
       
class AluguelViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    """
    Endpoint para Alugueis.
    - GET (list): Vê os seus alugueis confirmados.
    - GET (retrieve): Vê um aluguel específico.
    - POST (create): Cria um novo aluguel a partir de uma reserva pendente.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Alugueis.objects.none() 
    def get_queryset(self):
        """
        Filtra o queryset para retornar apenas
        os alugueis do utilizador logado.
        """
        try:
            usuario_perfil = self.request.user.usuarios
            return Alugueis.objects.filter(usuario=usuario_perfil)
        except Usuarios.DoesNotExist:
            return Alugueis.objects.none()

    def get_serializer_class(self):
        """
        Retorna o serializer correto dependendo da ação.
        Ação 'create' (POST) usa o serializer de criação.
        Outras ações (GET) usam o serializer de display.
        """
        if self.action == 'create':
            return AluguelCreateSerializer
        return AluguelSerializer 

    def get_serializer_context(self):
        """
        Passa o 'request' para o contexto do serializer.
        Necessário para o AluguelCreateSerializer aceder ao request.user.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        """
        Sobrescreve o método 'create' para que, ao criar,
        a resposta JSON use o serializer de display.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        aluguel_criado = serializer.save() 

        display_serializer = AluguelSerializer(aluguel_criado, context=self.get_serializer_context())
        headers = self.get_success_headers(display_serializer.data)
        
        return Response(display_serializer.data, status=status.HTTP_201_CREATED, headers=headers)