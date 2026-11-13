from django.db import models
from django.utils.translation import gettext_lazy as _

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