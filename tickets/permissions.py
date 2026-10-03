from rest_framework import permissions

class IsEspectador(permissions.IsAuthenticated):
    """Permiso exclusivo para clientes que compran entradas"""
    def has_permission(self, request, view):
        # Verifica que esté autenticado y que su rol sea ESPECTADOR
        return super().has_permission(request, view) and request.user.rol == 'ESPECTADOR'

class IsOrganizador(permissions.IsAuthenticated):
    """Permiso exclusivo para administradores de eventos"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.rol == 'ORGANIZADOR'

class IsOrganizador(permissions.BasePermission):
    message = "Acceso denegado. Solo las productoras u organizadores pueden hacer esto."

    def has_permission(self, request, view):
        # Verifica que exista el usuario, esté logueado y tenga el rol correcto
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.rol == 'ORGANIZADOR'
        )