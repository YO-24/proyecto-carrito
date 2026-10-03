from rest_framework import viewsets, views, status, permissions,generics
from rest_framework.response import Response
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Sector, Carro, ItemCarro, Orden, Ticket, Evento
from .permissions import IsEspectador,IsOrganizador
from drf_spectacular.utils import extend_schema
from .serializers import CarroSerializer, EventoSerializer, AgregarCarroSerializer,TicketSerializer,ItemCarroSerializer,SectorSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.views.decorators.csrf import csrf_exempt

# --- NUEVA VISTA PÚBLICA (Catálogo) ---
class EventoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint público para listar eventos y sus sectores.
    Solo permite métodos GET.
    """
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [permissions.AllowAny] # Acceso público sin token
    
    # Configuración de django-filter exigida en la rúbrica[cite: 1]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['recinto__nombre', 'fecha_hora'] # Filtros exactos
    search_fields = ['nombre', 'artista'] # Búsqueda por texto (ej: ?search=rock)

class CheckoutView(views.APIView):
    permission_classes = [IsEspectador]

class CarroViewSet(viewsets.ViewSet):
    # Protegido exclusivamente para espectadores
    permission_classes = [IsEspectador]

    def list(self, request):
        # Persistencia en BD: Obtiene el carro del usuario o lo crea si no existe[cite: 1]
        carro, created = Carro.objects.get_or_create(usuario=request.user)
        serializer = CarroSerializer(carro)
        return Response(serializer.data)

    @extend_schema(request=AgregarCarroSerializer)
    def create(self, request):
        carro, _ = Carro.objects.get_or_create(usuario=request.user)
        sector_id = request.data.get('sector_id')
        cantidad = int(request.data.get('cantidad', 1))
   
    def destroy(self, request, pk=None):
        from .models import ItemCarro
        try:
            # 1. Intentamos buscar por el ID directo del ítem, asegurando que sea del usuario logueado
            item = ItemCarro.objects.filter(pk=pk, carro__usuario=request.user).first()
            
            # 2. Si no lo encuentra, asumimos que el frontend envió el ID del Sector asociado
            if not item:
                item = ItemCarro.objects.filter(sector_id=pk, carro__usuario=request.user).first()
                
            # 3. Si por fin encontramos algo, lo borramos
            if item:
                item.delete()
                return Response({"mensaje": "Entrada eliminada del carro"}, status=200)
            else:
                return Response({"error": "No se encontró el ítem en tu carro"}, status=404)
                
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
        try:
            sector = Sector.objects.get(id=sector_id)
        except Sector.DoesNotExist:
            return Response({"error": "Sector no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        item, created = ItemCarro.objects.get_or_create(carro=carro, sector=sector, defaults={'cantidad': cantidad})
        if not created:
            item.cantidad += cantidad
            item.save()

        return Response({"mensaje": "Entrada agregada al carro persistente"}, status=status.HTTP_201_CREATED)

class CheckoutView(views.APIView):
    permission_classes = [IsEspectador]

    # El decorador atomic asegura que si algo falla, no se guarda nada a medias[cite: 1]
    @transaction.atomic 
    def post(self, request):
        carro, _ = Carro.objects.get_or_create(usuario=request.user)
        items = carro.items.all()

        if not items.exists():
            return Response({"error": "El carro está vacío"}, status=status.HTTP_400_BAD_REQUEST)

        # Genera el registro histórico inicial[cite: 1]
        orden = Orden.objects.create(usuario=request.user, estado='PENDIENTE')
        total_orden = 0

        for item in items:
            # select_for_update() bloquea la fila en PostgreSQL para evitar que dos personas compren la última entrada al mismo tiempo
            sector = Sector.objects.select_for_update().get(id=item.sector.id)
            
            # Validación de stock en el momento exacto del pago[cite: 1]
            if sector.stock_total < item.cantidad:
                transaction.set_rollback(True) # Revierte toda la transacción
                return Response({"error": f"Stock insuficiente para {sector.nombre}"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Descuento atómico[cite: 1]
            sector.stock_total -= item.cantidad
            sector.save()

            total_orden += (sector.precio * item.cantidad)

            # Emisión de tickets únicos[cite: 1]
            for _ in range(item.cantidad):
                Ticket.objects.create(orden=orden, sector=sector)
            
        # Transición a estado exitoso[cite: 1]
        orden.estado = 'PAGADO'
        orden.total = total_orden
        orden.save()
        
        # Limpiar el carro persistente después de comprar
        items.delete()

        return Response({"mensaje": "Checkout exitoso", "orden_id": orden.id}, status=status.HTTP_200_OK)

class MisTicketsView(APIView):
    permission_classes = [IsAuthenticated] # Solo usuarios logueados con JWT

    @extend_schema(responses=TicketSerializer(many=True))
    def get(self, request):
        # Filtramos tickets donde el usuario de la orden sea el que hace la petición y esté PAGADA
        tickets = Ticket.objects.filter(orden__usuario=request.user, orden__estado='PAGADO')
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)

class MiCarroView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ItemCarroSerializer(many=True))
    def get(self, request):
        items = ItemCarro.objects.filter(carro__usuario=request.user)
        serializer = ItemCarroSerializer(items, many=True)
        return Response(serializer.data)
    
class OrganizadorEventoView(APIView):
    permission_classes = [IsOrganizador] # <--- ¡Aquí está el guardia actuando!

    @extend_schema(request=EventoSerializer, responses=EventoSerializer)
    def post(self, request):
        serializer = EventoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "mensaje": "¡Evento creado con éxito en la cartelera!",
                "evento": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)

class OrganizadorSectorView(APIView):
    permission_classes = [IsOrganizador]

    def post(self, request):
        serializer = SectorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "mensaje": "¡Sector y entradas creadas con éxito!",
                "sector": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)

class ActualizarEstadoOrdenView(APIView):
    # permission_classes = [IsOrganizador]

    def patch(self, request, pk):
        orden = get_object_or_404(Orden, pk=pk)
        nuevo_estado = request.data.get('estado')
        estado_anterior = orden.estado

        # Validar que el estado enviado exista en las opciones (CHOICES)
        estados_permitidos = dict(Orden.ESTADOS).keys()
        if nuevo_estado not in estados_permitidos:
            return Response({"error": f"Estado no válido. Opciones: {list(estados_permitidos)}"}, status=400)

        if nuevo_estado == estado_anterior:
            return Response({"mensaje": "La orden ya tenía este estado."}, status=200)

        tickets = orden.tickets.all()

        # REGLA 1: Descontar stock al pasar a PAGADO
        if nuevo_estado == 'PAGADO' and estado_anterior in ['PENDIENTE', 'CANCELADO']:
            sectores_a_descontar = {}
            # Agrupar cuántas entradas se compraron por cada sector
            for ticket in tickets:
                sectores_a_descontar[ticket.sector] = sectores_a_descontar.get(ticket.sector, 0) + 1
            
            # Verificar disponibilidad antes de cobrar
            for sector, cantidad in sectores_a_descontar.items():
                if sector.stock_total < cantidad:
                    return Response({"error": f"Stock insuficiente en {sector.nombre}"}, status=400)
            
            # Aplicar el descuento en la base de datos
            for sector, cantidad in sectores_a_descontar.items():
                sector.stock_total -= cantidad
                sector.save()

        # REGLA 2: Reponer stock si la productora pasa la orden a CANCELADO
        elif nuevo_estado == 'CANCELADO' and estado_anterior in ['PAGADO', 'ENTREGADO']:
            sectores_a_reponer = {}
            for ticket in tickets:
                sectores_a_reponer[ticket.sector] = sectores_a_reponer.get(ticket.sector, 0) + 1
            
            # Devolver las entradas al pozo
            for sector, cantidad in sectores_a_reponer.items():
                sector.stock_total += cantidad
                sector.save()

        # Guardar el nuevo estado
        orden.estado = nuevo_estado
        orden.save()

        return Response({
            "mensaje": "Estado actualizado exitosamente",
            "orden": orden.id,
            "nuevo_estado": orden.estado
        }, status=200)
class MiTokenPersonalizadoSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Agregamos el claim personalizado exigido en la pauta
        token['rol'] = user.rol
        return token

class LoginPersonalizadoView(TokenObtainPairView):
    serializer_class = MiTokenPersonalizadoSerializer
    