from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class Usuario(AbstractUser):
    ROLES = (
        ('ESPECTADOR', 'Espectador'),
        ('ORGANIZADOR', 'Organizador'),
    )
    rol = models.CharField(max_length=15, choices=ROLES, default='ESPECTADOR')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

class Recinto(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Recinto'
        verbose_name_plural = 'Recintos'

    def __str__(self):
        return self.nombre

class Evento(models.Model):
    nombre = models.CharField(max_length=150)
    artista = models.CharField(max_length=150)
    fecha_hora = models.DateTimeField()
    recinto = models.ForeignKey(Recinto, on_delete=models.CASCADE, related_name='eventos')

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f"{self.nombre} - {self.artista}"

class Sector(models.Model):
    evento = models.ForeignKey(Evento, related_name='sectores', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50) 
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    stock_total = models.PositiveIntegerField() 

    class Meta:
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectores'

    def __str__(self):
        return f"{self.nombre} ({self.evento.nombre})"

class Carro(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='carro')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Carro'
        verbose_name_plural = 'Carros'
        
    def __str__(self):
        return f"Carro de {self.usuario.username}"

class ItemCarro(models.Model):
    carro = models.ForeignKey(Carro, on_delete=models.CASCADE, related_name='items')
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    # AGREGA ESTO:
    class Meta:
        verbose_name = "Ítem de Carro"
        verbose_name_plural = "Ítems de Carro"

    def __str__(self):
        return f"{self.cantidad} x {self.sector.nombre}"

class Orden(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='ordenes')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    creado_en = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        
    def __str__(self):
        return f"Orden #{self.id} - {self.estado}"

class Ticket(models.Model):
    orden = models.ForeignKey(Orden, related_name='tickets', on_delete=models.CASCADE)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    codigo_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        
    def __str__(self):
        return f"Ticket {self.codigo_uuid} - {self.sector.nombre}"