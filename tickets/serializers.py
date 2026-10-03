from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Recinto, Usuario, Evento, Sector, Carro, ItemCarro
from .models import Ticket
from .models import ItemCarro

# 1. Personalización del Token JWT con el Rol
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Aquí inyectamos el claim del rol exigido en la evaluación
        token['rol'] = user.rol
        return token

# 2. Serializadores de Catálogo
class SectorSerializer(serializers.ModelSerializer):
    # 1. Obligamos a Django a aceptar el ID del evento que viene desde el HTML
    evento = serializers.PrimaryKeyRelatedField(queryset=Evento.objects.all())

    class Meta:
        model = Sector
        # 2. Asegúrate de que la palabra 'evento' esté dentro de esta lista
        fields = ['id', 'evento', 'nombre', 'precio', 'stock_total']
        
class EventoSerializer(serializers.ModelSerializer):
    sectores = SectorSerializer(many=True, read_only=True)
    recinto = serializers.PrimaryKeyRelatedField(queryset=Recinto.objects.all())

    class Meta:
        model = Evento
        # Si 'recinto' no está escrito en esta lista exacta, Django lo ignora por completo
        fields = ['id', 'nombre', 'artista', 'fecha_hora', 'recinto', 'sectores']

# 3. Serializadores del Carro
class ItemCarroSerializer(serializers.ModelSerializer):
    sector_nombre = serializers.ReadOnlyField(source='sector.nombre')
    precio_unitario = serializers.ReadOnlyField(source='sector.precio')

    class Meta:
        model = ItemCarro
        fields = ['id', 'sector', 'sector_nombre', 'precio_unitario', 'cantidad']

class CarroSerializer(serializers.ModelSerializer):
    items = ItemCarroSerializer(many=True, read_only=True)

    class Meta:
        model = Carro
        fields = ['id', 'usuario', 'creado_en', 'items']

class AgregarCarroSerializer(serializers.Serializer):
    sector_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(default=1)

class TicketSerializer(serializers.ModelSerializer):
    evento_nombre = serializers.CharField(source='sector.evento.nombre', read_only=True)
    evento_fecha = serializers.DateTimeField(source='sector.evento.fecha_hora', read_only=True)
    sector_nombre = serializers.CharField(source='sector.nombre', read_only=True)

    class Meta:
        model = Ticket
        fields = ['codigo_uuid', 'evento_nombre', 'evento_fecha', 'sector_nombre']

class ItemCarroSerializer(serializers.ModelSerializer):
    evento_nombre = serializers.CharField(source='sector.evento.nombre', read_only=True)
    sector_nombre = serializers.CharField(source='sector.nombre', read_only=True)
    precio_unitario = serializers.DecimalField(source='sector.precio', max_digits=10, decimal_places=0, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemCarro
        fields = ['id', 'evento_nombre', 'sector_nombre', 'cantidad', 'precio_unitario', 'subtotal']

    def get_subtotal(self, obj):
        return obj.cantidad * obj.sector.precio