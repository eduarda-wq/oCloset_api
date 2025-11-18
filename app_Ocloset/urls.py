from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'roupas', views.RoupaViewSet, basename='roupa')
router.register(r'roupas-imagens', views.RoupaImagemViewSet, basename='roupaimagem')
router.register(r'reservas', views.ReservaViewSet, basename='reserva')
router.register(r'alugueis', views.AluguelViewSet, basename='aluguel')

urlpatterns = [
    path('', include(router.urls)),
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),
    path('login/', obtain_auth_token, name='login'),
    path('perfil/', views.UserProfileView.as_view(), name='perfil'),
]