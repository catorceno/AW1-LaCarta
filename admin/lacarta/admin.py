from django.contrib import admin
from .models import Restaurante, Plato, Pedido, ItemPedido

# Register your models here.
class PlatoInline(admin.TabularInline):
    model = Plato

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    readonly_fields = ('precio_unitario',)
    extra = 1

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

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = (ItemPedidoInline,)
    list_display = ('id', 'cliente', 'restaurante', 'estado', 'fecha', 'total')
    list_filter = ('estado', 'restaurante')
    search_fields = ('cliente',)
    readonly_fields = ('total', 'fecha')

    def save_formset(self, request, form, formset, change):
        """Al guardar los ítems: congela el precio de los nuevos y recalcula el total."""
        items = formset.save(commit=False)
        for item in items:
            if item.pk is None:                         # ítem nuevo: copia el precio actual del plato
                item.precio_unitario = item.plato.precio
            item.save()
        for item in formset.deleted_objects:
            item.delete()

        pedido = form.instance
        pedido.total = sum(i.cantidad * i.precio_unitario for i in pedido.items.all())
        pedido.save(update_fields=['total'])