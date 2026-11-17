from sqlalchemy import func, select

from ..models import Plato, Restaurante
from .base import Repositorio


class RestauranteRepository(Repositorio):
    """Todas las consultas de restaurantes y de sus platos."""

    def get(self, restaurante_id):
        return self.session.get(Restaurante, restaurante_id)

    def listar_con_cantidad_de_platos(self, ciudad=""):
        """[(Restaurante, cantidad de platos)] por nombre; filtra por ciudad si llega una."""
        consulta = (
            self.session.query(Restaurante, func.count(Plato.id).label("cantidad"))
            .outerjoin(Plato)
            .group_by(Restaurante.id)
        )
        if ciudad:
            consulta = consulta.filter(Restaurante.ciudad.ilike(f"%{ciudad}%"))
        return consulta.order_by(Restaurante.nombre).all()

    def platos_de(self, restaurante_id):
        return self.session.scalars(
            select(Plato).filter_by(restaurante_id=restaurante_id).order_by(Plato.nombre)
        ).all()

    def platos_por_id(self, ids):
        """{id: Plato} de los platos que existen; los que no existen no aparecen."""
        return {p.id: p for p in self.session.scalars(select(Plato).where(Plato.id.in_(ids)))}

    def add(self, restaurante):
        self.session.add(restaurante)

    def add_plato(self, plato):
        self.session.add(plato)

    def delete(self, restaurante):
        self.session.delete(restaurante)
