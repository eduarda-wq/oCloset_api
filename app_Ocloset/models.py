from django.db import models
from django.contrib.auth.models import User

class Alugueis(models.Model):
    reserva = models.ForeignKey('Reservas', models.DO_NOTHING, blank=True, null=True)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    roupa = models.ForeignKey('Roupas', models.DO_NOTHING, blank=True, null=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    status = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'alugueis'


class Avaliacoes(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    roupa = models.ForeignKey('Roupas', models.DO_NOTHING, blank=True, null=True)
    nota = models.IntegerField(blank=True, null=True)
    comentario = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'avaliacoes'


class Comentarios(models.Model):
    roupa = models.ForeignKey('Roupas', models.DO_NOTHING)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    comentario = models.TextField()

    class Meta:
        managed = False
        db_table = 'comentarios'


class Favoritos(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING, blank=True, null=True)
    roupa = models.ForeignKey('Roupas', models.DO_NOTHING, blank=True, null=True)
    criado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'favoritos'
        unique_together = (('usuario', 'roupa'),)


class Pagamentos(models.Model):
    reserva = models.ForeignKey('Reservas', models.DO_NOTHING)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=50)
    status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pagamentos'


class Reservas(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    roupa = models.ForeignKey('Roupas', models.DO_NOTHING)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reservas'


class Roupas(models.Model):
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    marca = models.CharField(max_length=100, blank=True, null=True)
    cor = models.CharField(max_length=50, blank=True, null=True)
    tamanho = models.CharField(max_length=20, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    cuidados = models.TextField(blank=True, null=True)
    ocasiao = models.CharField(max_length=100, blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roupas'


class RoupasImagens(models.Model):
    roupa = models.ForeignKey(Roupas, models.DO_NOTHING)
    url = models.TextField()
    criado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roupas_imagens'


class Usuarios(models.Model):
    
    user = models.OneToOneField(User, models.DO_NOTHING, blank=True, null=True)
    
    nome = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=150)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cpf = models.CharField(unique=True, max_length=14, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    criado_em = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        """
        Retorna uma representação legível do objeto.
        Usado pela API para mostrar o nome em vez do ID.
        """
        return self.nome
    
    class Meta:
        managed = False
        db_table = 'usuarios'
