from rest_framework import permissions
from .models import Usuarios

class IsRoupaOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão personalizada para permitir que apenas os donos de uma roupa
    possam editá-la ou apagá-la.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        try:
            usuario_perfil = Usuarios.objects.get(user=request.user)
        except Usuarios.DoesNotExist:
            return False 

        return obj.usuario == usuario_perfil


class IsRoupaImagemOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão personalizada para permitir que apenas os donos da ROUPA PAI
    possam editar ou apagar uma imagem.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        if not request.user.is_authenticated:
            return False

        try:
            usuario_perfil = Usuarios.objects.get(user=request.user)
        except Usuarios.DoesNotExist:
            return False

        return obj.roupa.usuario == usuario_perfil