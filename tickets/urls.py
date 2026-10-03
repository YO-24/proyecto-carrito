from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarroViewSet, CheckoutView, EventoViewSet
from .views import MisTicketsView
from .views import MiCarroView
from .views import OrganizadorEventoView,OrganizadorSectorView
from .views import ActualizarEstadoOrdenView
from .views import LoginPersonalizadoView

# El router genera automáticamente GET /api/eventos/ y GET /api/eventos/{id}/
router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento')

urlpatterns = [
    # Rutas públicas generadas por el router
    path('', include(router.urls)),
    
    # Rutas privadas del Espectador
    path('carro-tickets/', CarroViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('compras/pagar/', CheckoutView.as_view()),
    path('mis-tickets/', MisTicketsView.as_view(), name='mis-tickets'),
    path('mi-carro/', MiCarroView.as_view(), name='mi-carro'),
    path('organizador/eventos/', OrganizadorEventoView.as_view(), name='crear-evento'),
    path('organizador/sectores/', OrganizadorSectorView.as_view(), name='crear-sector'),
    path('login/', LoginPersonalizadoView.as_view(), name='login_token'),
]