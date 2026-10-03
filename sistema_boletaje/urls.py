from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from tickets.serializers import CustomTokenObtainPairSerializer
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# 1. Vista con la interfaz gráfica limpia de DRF
@api_view(['GET'])
def api_root(request):
    return Response({
        "servicio": "SaaS Boletaje API",
        "estado": "Operativo",
        "desarrollador": "Fernando Soto Navarrete",
        "año": 2026
    })

def catch_all_404(request, path_invalido):
    return JsonResponse({"error": f"Endpoint '/{path_invalido}' no existe"}, status=404)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path('', api_root, name='inicio'),
    path('admin/', admin.site.urls),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('tickets.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    re_path(r'^(?P<path_invalido>.*)$', catch_all_404),

]