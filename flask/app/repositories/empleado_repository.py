from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..models import Empleado
from .base import Repositorio


class EmpleadoRepository(Repositorio):
    """Todas las consultas de empleados."""

    def get(self, empleado_id):
        return self.session.get(Empleado, empleado_id)

    def listar(self):
        """Todos, por apellido y nombre, con su restaurante."""
        return self.session.scalars(
            select(Empleado)
            .options(joinedload(Empleado.restaurante))
            .order_by(Empleado.apellido, Empleado.nombre)
        ).all()

    def add(self, empleado):
        self.session.add(empleado)

    def delete(self, empleado):
        self.session.delete(empleado)
