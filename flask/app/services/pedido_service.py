"""Casos de uso de pedidos: el cliente arma y cancela los suyos; la cocina avanza la cola.

Todas las reglas del enunciado viven aquí, en un solo lugar. Ocultar botones
en las plantillas es solo comodidad.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ..errors import NoEncontradoError, ReglaDeNegocioError
from ..models import ItemPedido, Pedido

CANTIDAD_MAXIMA = 20

ETIQUETAS_ESTADO = {
    "pendiente": "Pendiente",
    "en_preparacion": "En preparación",
    "listo": "Listo",
    "entregado": "Entregado",
    "cancelado": "Cancelado",
}

# La tabla de estados del enunciado. La cocina solo avanza un paso hacia
# adelante; cualquier otra transición se rechaza (por ejemplo, listo -> pendiente).
SIGUIENTE_ESTADO = {
    "pendiente": "en_preparacion",
    "en_preparacion": "listo",
    "listo": "entregado",
}
ESTADOS_ACTIVOS = tuple(SIGUIENTE_ESTADO)   # los que ve la cocina

# ------------------------------------------------------------------ DTO de entrada (los arma el controlador)


@dataclass(frozen=True)
class LineaPedido:
    plato_id: int
    cantidad: int


@dataclass(frozen=True)
class PedidoDetails:
    """Solo plato y cantidad (R1.4). El cliente sale del token; precios y total, del servidor."""
    restaurante_id: int
    lineas: tuple[LineaPedido, ...]


# ------------------------------------------------------------------ DTO de salida (los recibe la plantilla)


@dataclass(frozen=True)
class ItemView:
    cantidad: int
    plato_nombre: str
    precio_unitario: Decimal


@dataclass(frozen=True)
class PedidoView:
    id: int
    estado: str
    estado_etiqueta: str
    fecha: datetime
    total: Decimal
    restaurante_id: int
    restaurante_nombre: str
    items: tuple[ItemView, ...]
    siguiente_estado: str | None      # None si la cocina ya no lo puede avanzar
    siguiente_etiqueta: str | None


@dataclass(frozen=True)
class PedidoResumen:
    """Una fila de "Mis pedidos" (sin los ítems)."""
    id: int
    estado: str
    estado_etiqueta: str
    total: Decimal
    restaurante_nombre: str


def _etiqueta(estado):
    """'en_preparacion' -> 'En preparación'."""
    return ETIQUETAS_ESTADO.get(estado, estado)


def _a_view(pedido):
    siguiente = SIGUIENTE_ESTADO.get(pedido.estado)
    return PedidoView(
        id=pedido.id,
        estado=pedido.estado,
        estado_etiqueta=_etiqueta(pedido.estado),
        fecha=pedido.fecha,
        total=pedido.total,
        restaurante_id=pedido.restaurante_id,
        restaurante_nombre=pedido.restaurante.nombre,
        items=tuple(
            ItemView(cantidad=i.cantidad, plato_nombre=i.plato.nombre, precio_unitario=i.precio_unitario)
            for i in pedido.items
        ),
        siguiente_estado=siguiente,
        siguiente_etiqueta=_etiqueta(siguiente) if siguiente else None,
    )


def _a_resumen(pedido):
    return PedidoResumen(
        id=pedido.id,
        estado=pedido.estado,
        estado_etiqueta=_etiqueta(pedido.estado),
        total=pedido.total,
        restaurante_nombre=pedido.restaurante.nombre,
    )


# ------------------------------------------------------------------ servicio


class PedidoService:
    """Un método por caso de uso. Decide cuándo hacer commit."""

    def __init__(self, pedidos, restaurantes):
        self.pedidos = pedidos
        self.restaurantes = restaurantes

    def _propio(self, pedido_id, cliente):
        """404 y no 403 si es de otro: un 403 confirmaría que ese pedido existe (R2.6)."""
        pedido = self.pedidos.get_de_cliente(pedido_id, cliente)
        if pedido is None:
            raise NoEncontradoError(f"No existe el pedido {pedido_id}.")
        return pedido

    # -------------------------------------------------------------- cliente

    def crear(self, cliente, details):
        """Crea el pedido con todos sus ítems, o no crea nada (R1). Devuelve su id."""
        restaurante = self.restaurantes.get(details.restaurante_id)
        if restaurante is None:
            raise NoEncontradoError(f"No existe el restaurante {details.restaurante_id}.")

        # 1. Cantidades (R1.5)
        for linea in details.lineas:
            if not 1 <= linea.cantidad <= CANTIDAD_MAXIMA:
                raise ReglaDeNegocioError(f"La cantidad debe estar entre 1 y {CANTIDAD_MAXIMA}.")
        if not details.lineas:
            raise ReglaDeNegocioError("Elige al menos un plato.")

        # 2. Validar cada plato antes de escribir nada (R1.5)
        platos = self.restaurantes.platos_por_id([linea.plato_id for linea in details.lineas])
        for linea in details.lineas:
            plato = platos.get(linea.plato_id)
            if plato is None:
                raise NoEncontradoError(f"No existe el plato {linea.plato_id}.")       # R1.7
            if plato.restaurante_id != restaurante.id:
                raise ReglaDeNegocioError(f"{plato.nombre} es de otro restaurante.")
            if not plato.disponible:
                raise ReglaDeNegocioError(f"{plato.nombre} no está disponible.")

        # 3. Armar el pedido: cliente desde el token, precio congelado, total en el servidor
        pedido = Pedido(cliente=cliente, restaurante_id=restaurante.id)          # R1.2
        total = Decimal("0")
        for linea in details.lineas:
            plato = platos[linea.plato_id]
            pedido.items.append(ItemPedido(
                plato_id=plato.id,
                cantidad=linea.cantidad,
                precio_unitario=plato.precio,         # copia del precio de hoy (R1.3)
            ))
            total += plato.precio * linea.cantidad
        pedido.total = total                          # R1.4

        # 4. Un solo commit: el pedido y todos sus ítems, o nada (R1.5)
        self.pedidos.add(pedido)
        self.pedidos.commit()
        return pedido.id

    def mis_pedidos(self, cliente):
        return [_a_resumen(p) for p in self.pedidos.listar_de_cliente(cliente)]

    def obtener_propio(self, pedido_id, cliente):
        return _a_view(self._propio(pedido_id, cliente))

    def cancelar(self, pedido_id, cliente):
        """pendiente -> cancelado, solo el dueño del pedido."""
        pedido = self._propio(pedido_id, cliente)
        if pedido.estado != "pendiente":
            raise ReglaDeNegocioError("Solo se puede cancelar un pedido pendiente.")
        pedido.estado = "cancelado"
        self.pedidos.commit()

    # -------------------------------------------------------------- cocina

    def cola_de_cocina(self):
        return [_a_view(p) for p in self.pedidos.listar_con_estados(ESTADOS_ACTIVOS)]

    def avanzar(self, pedido_id, nuevo):
        """Solo se acepta el siguiente paso de la tabla. Devuelve la etiqueta del nuevo estado."""
        pedido = self.pedidos.get(pedido_id)
        if pedido is None:
            raise NoEncontradoError(f"No existe el pedido {pedido_id}.")
        if SIGUIENTE_ESTADO.get(pedido.estado) != nuevo:
            raise ReglaDeNegocioError(f"No se puede pasar de {pedido.estado} a {nuevo or '(vacío)'}.")
        pedido.estado = nuevo
        self.pedidos.commit()
        return _etiqueta(nuevo)
