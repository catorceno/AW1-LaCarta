# 1.
# nueva tabla empleados -> CRUD
# la nueva tabla debe reflejarse tanto en django como en flask, cualquier modificación se debe poder realizar después de un login

# 2.
# se debe loguear para editar esa tabla (tanto en django como flask)
# si no logueado -> solo get, también para los roles de cliente y cocina
# solo el rol admin de auth0 debe poder manipular esta tabla (hacer el CRUD completo)

# 3.
# login de django y flask debe ser el mismo, el login debe ser desde Auth0

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
    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT, related_name='pedidos')
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

class Empleado(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT, related_name='empleados')
    nombre = models.CharField(_('nombre'), max_length=120)
    apellido = models.CharField(_('apellido'), max_length=120)
    ci = models.CharField(_('C.I.'), max_length=12, unique=True)
    correo = models.EmailField(_('correo'), blank=True, null=True)
    telefono = models.CharField(_('teléfono'), max_length=30, blank=True, null=True)
    direccion = models.CharField(_('dirección'), max_length=200, blank=True, null=True)
    salario = models.DecimalField(_('salario'), max_digits=10, decimal_places=2)
    fecha_ingreso = models.DateField(_('fecha ingreso'), db_default=Now())
    activo = models.BooleanField(_('activo'), default=True, db_default=True) # para cuando lo despiden

    def __str__(self):
        return f'{self.nombre} {self.apellido}'

    class Meta:
        ordering = ['apellido', 'nombre']
        constraints = [
            models.CheckConstraint(condition=models.Q(salario__gte=0), name='empleado_salario_no_negativo')
        ]