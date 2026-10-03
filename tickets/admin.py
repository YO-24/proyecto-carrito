from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Recinto, Evento, Sector, Carro, ItemCarro, Orden, Ticket
from django.contrib.auth.models import Group

# 1. Configuración personalizada
class CustomUsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Configuración de BoleteraSO', {'fields': ('rol',)}),
    )
    list_display = ('username', 'email', 'rol', 'is_staff')

# 2. ÚNICO REGISTRO DEL USUARIO (Borra cualquier otro que diga admin.site.register(Usuario...))
admin.site.register(Usuario, CustomUsuarioAdmin)

# 3. El resto de tus modelos normales
admin.site.register(Recinto)
admin.site.register(Evento)
admin.site.register(Sector)
admin.site.register(Carro)
admin.site.register(ItemCarro)
admin.site.register(Orden)
admin.site.register(Ticket)
admin.site.unregister(Group)