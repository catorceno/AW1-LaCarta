from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Now

class Restaurante(models.Model):
    nombre = models.CharField(_('nombre'), max_length=120)
    ciudad = models.CharField(_('ciudad'), max_length=80)
    direccion = models.CharField(_('dirección'), max_length=200, blank=True, null=True)
    telefono = models.CharField(_('teléfono'), max_length=30, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Plato(models.Model):
    nombre = models.CharField(_('nombre'), max_length=120)
    precio = models.DecimalField(_('precio'), max_digits=10, decimal_places=2)
    disponible = models.BooleanField(_('disponible'), default=True, db_default=True)

    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='platos')

    def __str__(self):
        return self.nombre

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(precio__gt=0), name='plato_precio_positivo')
        ]

class Estado(models.TextChoices):
    PENDIENTE = 'pendiente', _('Pendiente')
    EN_PREPARACION = 'en_preparacion', _('En preparación')
    LISTO = 'listo', _('Listo')
    ENTREGADO = 'entregado', _('Entregado')
    CANCELADO = 'cancelado', _('Cancelado')

class Pedido(models.Model):

    cliente = models.CharField(_('cliente'), max_length=255)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT)
    estado = models.CharField(_('estado'), max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, db_default=Estado.PENDIENTE)
    fecha = models.DateTimeField(_('fecha'), db_default=Now())
    total = models.DecimalField(_('total'), max_digits=10, decimal_places=2, default=0, db_default=0)

    def __str__(self):
        return f'Pedido #{self.id}'

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(estado__in=Estado.values), name='pedido_estado_valido'),
            models.CheckConstraint(condition=models.Q(total__gte=0), name='pedido_total_no_negativo')
        ]

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    plato = models.ForeignKey(Plato, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(_('cantidad'))
    precio_unitario = models.DecimalField(_('precio unitario'), max_digits=10, decimal_places=2)

    def __str__(self):
            return f'Item Pedido {self.cantidad} x {self.plato}'

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='itempedido_cantidad_positivo'),
            models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name='itempedido_preciounitario_no_negativo')
        ]