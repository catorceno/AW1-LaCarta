"""Casos de uso de empleados. Quién puede llamar a cada uno lo decide la presentación
con @requires_auth; aquí solo están las reglas de los datos."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..errors import ConflictoError, NoEncontradoError, ReglaDeNegocioError
from ..models import Empleado

CI_MAXIMO = 12

# ------------------------------------------------------------------ DTO de entrada (los arma el controlador)


@dataclass(frozen=True)
class EmpleadoDetails:
    nombre: str
    apellido: str
    ci: str
    restaurante_id: int
    salario: Decimal
    fecha_ingreso: date | None = None     # None: al crear la pone Postgres; al editar se mantiene
    correo: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    activo: bool = True


# ------------------------------------------------------------------ DTO de salida (los recibe la plantilla)


@dataclass(frozen=True)
class EmpleadoPublicoView:
    """Lo que puede ver cualquiera, sin login."""
    id: int
    nombre: str
    apellido: str
    activo: bool
    restaurante_id: int
    restaurante_nombre: str


@dataclass(frozen=True)
class EmpleadoView:
    """Con los datos privados: solo para quien administra empleados."""
    id: int
    nombre: str
    apellido: str
    ci: str
    correo: str | None
    telefono: str | None
    direccion: str | None
    salario: Decimal
    fecha_ingreso: date
    activo: bool
    restaurante_id: int
    restaurante_nombre: str


def _a_publico(empleado):
    return EmpleadoPublicoView(
        id=empleado.id,
        nombre=empleado.nombre,
        apellido=empleado.apellido,
        activo=empleado.activo,
        restaurante_id=empleado.restaurante_id,
        restaurante_nombre=empleado.restaurante.nombre,
    )


def _a_view(empleado):
    return EmpleadoView(
        id=empleado.id,
        nombre=empleado.nombre,
        apellido=empleado.apellido,
        ci=empleado.ci,
        correo=empleado.correo,
        telefono=empleado.telefono,
        direccion=empleado.direccion,
        salario=empleado.salario,
        fecha_ingreso=empleado.fecha_ingreso,
        activo=empleado.activo,
        restaurante_id=empleado.restaurante_id,
        restaurante_nombre=empleado.restaurante.nombre,
    )


def _campos(details):
    """Los campos a escribir. Sin fecha_ingreso si llegó vacía."""
    campos = {
        "nombre": details.nombre,
        "apellido": details.apellido,
        "ci": details.ci,
        "restaurante_id": details.restaurante_id,
        "salario": details.salario,
        "fecha_ingreso": details.fecha_ingreso,
        "correo": details.correo,
        "telefono": details.telefono,
        "direccion": details.direccion,
        "activo": details.activo,
    }
    if campos["fecha_ingreso"] is None:
        del campos["fecha_ingreso"]
    return campos


# ------------------------------------------------------------------ servicio


class EmpleadoService:
    """Un método por caso de uso. Decide cuándo hacer commit."""

    def __init__(self, empleados, restaurantes):
        self.empleados = empleados
        self.restaurantes = restaurantes

    def _buscar(self, empleado_id):
        empleado = self.empleados.get(empleado_id)
        if empleado is None:
            raise NoEncontradoError(f"No existe el empleado {empleado_id}.")
        return empleado

    def _validar(self, details):
        if not details.nombre or not details.apellido or not details.ci:
            raise ReglaDeNegocioError("Nombre, apellido y C.I. son obligatorios.")
        if len(details.ci) > CI_MAXIMO:
            raise ReglaDeNegocioError(f"El C.I. tiene como máximo {CI_MAXIMO} caracteres.")
        if self.restaurantes.get(details.restaurante_id) is None:
            raise ReglaDeNegocioError("El restaurante elegido no existe.")
        if details.salario < 0:
            raise ReglaDeNegocioError("El salario no puede ser negativo.")

    def _guardar(self):
        try:
            self.empleados.commit()
        except ConflictoError as err:
            raise ReglaDeNegocioError("Ya existe un empleado con ese C.I.") from err

    def listar(self, privados=False):
        """privados=False: solo los datos públicos de cada empleado."""
        a_view = _a_view if privados else _a_publico
        return [a_view(e) for e in self.empleados.listar()]

    def obtener(self, empleado_id, privados=False):
        a_view = _a_view if privados else _a_publico
        return a_view(self._buscar(empleado_id))

    def crear(self, details):
        self._validar(details)
        empleado = Empleado(**_campos(details))
        self.empleados.add(empleado)
        self._guardar()
        return _a_view(empleado)

    def actualizar(self, empleado_id, details):
        empleado = self._buscar(empleado_id)
        self._validar(details)
        for campo, valor in _campos(details).items():
            setattr(empleado, campo, valor)
        self._guardar()
        return _a_view(empleado)

    def eliminar(self, empleado_id):
        self.empleados.delete(self._buscar(empleado_id))
        self.empleados.commit()
