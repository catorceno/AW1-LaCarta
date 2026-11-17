from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from ..models import ItemPedido, Pedido
from .base import Repositorio

# El pedido con su restaurante y sus ítems (cada uno con su plato) en pocas consultas
_CON_ITEMS = (
    joinedload(Pedido.restaurante),
    selectinload(Pedido.items).joinedload(ItemPedido.plato),
)


class PedidoRepository(Repositorio):
    """Todas las consultas de pedidos."""

    def get(self, pedido_id):
        return self.session.get(Pedido, pedido_id)

    def get_de_cliente(self, pedido_id, cliente):
        """El pedido si es de ese cliente; None si no existe o es de otro."""
        return self.session.scalars(
            select(Pedido).options(*_CON_ITEMS).filter_by(id=pedido_id, cliente=cliente)
        ).first()

    def listar_de_cliente(self, cliente):
        """Los pedidos del cliente, el más reciente primero."""
        return self.session.scalars(
            select(Pedido)
            .options(joinedload(Pedido.restaurante))
            .filter_by(cliente=cliente)
            .order_by(Pedido.fecha.desc())
        ).all()

    def listar_con_estados(self, estados):
        """Los pedidos en alguno de esos estados, el más antiguo primero."""
        return self.session.scalars(
            select(Pedido)
            .options(*_CON_ITEMS)
            .where(Pedido.estado.in_(estados))
            .order_by(Pedido.fecha)
        ).all()

    def add(self, pedido):
        self.session.add(pedido)
