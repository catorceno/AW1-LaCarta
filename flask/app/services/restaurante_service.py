"""Casos de uso de la carta: restaurantes y sus platos."""
from dataclasses import dataclass
from decimal import Decimal

from ..errors import NoEncontradoError
from ..models import Plato, Restaurante

# ------------------------------------------------------------------ DTO de entrada (los arma el controlador)


@dataclass(frozen=True)
class RestauranteDetails:
    nombre: str
    ciudad: str
    direccion: str | None = None
    telefono: str | None = None


@dataclass(frozen=True)
class PlatoDetails:
    nombre: str
    precio: Decimal
    disponible: bool = True


# ------------------------------------------------------------------ DTO de salida (los recibe la plantilla)


@dataclass(frozen=True)
class RestauranteView:
    id: int
    nombre: str
    ciudad: str
    direccion: str | None
    telefono: str | None


@dataclass(frozen=True)
class RestauranteResumen:
    """Una fila del listado."""
    id: int
    nombre: str
    ciudad: str
    cantidad_platos: int


@dataclass(frozen=True)
class PlatoView:
    id: int
    nombre: str
    precio: Decimal
    disponible: bool


def a_view(restaurante):
    return RestauranteView(
        id=restaurante.id,
        nombre=restaurante.nombre,
        ciudad=restaurante.ciudad,
        direccion=restaurante.direccion,
        telefono=restaurante.telefono,
    )


def _plato_a_view(plato):
    return PlatoView(id=plato.id, nombre=plato.nombre, precio=plato.precio, disponible=plato.disponible)


# ------------------------------------------------------------------ servicio


class RestauranteService:
    """Un método por caso de uso. Decide cuándo hacer commit."""

    def __init__(self, restaurantes):
        self.restaurantes = restaurantes

    def _buscar(self, restaurante_id):
        restaurante = self.restaurantes.get(restaurante_id)
        if restaurante is None:
            raise NoEncontradoError(f"No existe el restaurante {restaurante_id}.")
        return restaurante

    def listar(self, ciudad=""):
        return [
            RestauranteResumen(id=r.id, nombre=r.nombre, ciudad=r.ciudad, cantidad_platos=cantidad)
            for r, cantidad in self.restaurantes.listar_con_cantidad_de_platos(ciudad)
        ]

    def obtener(self, restaurante_id):
        return a_view(self._buscar(restaurante_id))

    def carta(self, restaurante_id):
        """El restaurante y sus platos por nombre."""
        restaurante = self._buscar(restaurante_id)
        platos = [_plato_a_view(p) for p in self.restaurantes.platos_de(restaurante.id)]
        return a_view(restaurante), platos

    def crear(self, details):
        restaurante = Restaurante(
            nombre=details.nombre,
            ciudad=details.ciudad,
            direccion=details.direccion,
            telefono=details.telefono,
        )
        self.restaurantes.add(restaurante)
        self.restaurantes.commit()
        return a_view(restaurante)

    def actualizar(self, restaurante_id, details):
        restaurante = self._buscar(restaurante_id)
        restaurante.nombre = details.nombre
        restaurante.ciudad = details.ciudad
        restaurante.direccion = details.direccion
        restaurante.telefono = details.telefono
        self.restaurantes.commit()
        return a_view(restaurante)

    def eliminar(self, restaurante_id):
        self.restaurantes.delete(self._buscar(restaurante_id))
        self.restaurantes.commit()

    def agregar_plato(self, restaurante_id, details):
        restaurante = self._buscar(restaurante_id)
        plato = Plato(
            nombre=details.nombre,
            precio=details.precio,
            disponible=details.disponible,
            restaurante_id=restaurante.id,
        )
        self.restaurantes.add_plato(plato)
        self.restaurantes.commit()
        return _plato_a_view(plato)
