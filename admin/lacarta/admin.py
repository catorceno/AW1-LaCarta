from django.contrib import admin
from .models import Restaurante, Plato

# Register your models here.
class PlatoInline(admin.TabularInline):
    model = Plato


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    inlines = (PlatoInline,)
    list_display = ('nombre', 'ciudad', 'direccion', 'telefono')
    list_filter = ('ciudad',)
    search_fields = ('nombre',)

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'restaurante', 'precio', 'disponible')
    list_filter = ('disponible',)