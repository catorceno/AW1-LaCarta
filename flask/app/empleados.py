"""API de empleados: lectura pública; crear, editar y borrar solo con los permisos de Auth0.

- Sin token, o con los roles cliente y cocina: solo los datos públicos
  (nombre, apellido, restaurante, activo).
- write:empleados: crear, editar y recibir los datos privados (CI, salario, contacto).
- delete:empleados: borrar.

Las reglas de los datos están en services/empleado_service.py.
"""
from datetime import date

from flask import Blueprint

from .auth import optional_payload, requires_auth
from .extensions import db
from .repositories import EmpleadoRepository, RestauranteRepository
from .respuestas import cuerpo_json, decimal, entero, error_json, json_de, texto, texto_opcional
from .services.empleado_service import EmpleadoDetails, EmpleadoService

bp = Blueprint("empleados", __name__, url_prefix="/api")


def servicio():
    return EmpleadoService(EmpleadoRepository(db.session), RestauranteRepository(db.session))


def ve_datos_privados():
    payload = optional_payload()
    return payload is not None and "write:empleados" in payload.get("permissions", [])


def leer_empleado(datos):
    """Convierte el JSON a un EmpleadoDetails, o lanza ValueError con el motivo.

    Aquí solo se revisa el formato; las reglas (obligatorios, C.I., salario,
    restaurante) las revisa el servicio.
    """
    restaurante_id = entero(datos.get("restaurante_id"), "Elige un restaurante.")
    salario = decimal(datos.get("salario"), "El salario debe ser un número.")

    texto_fecha = texto(datos, "fecha_ingreso")
    try:
        fecha_ingreso = date.fromisoformat(texto_fecha) if texto_fecha else None
    except ValueError:
        raise ValueError("La fecha de ingreso no es válida.")

    return EmpleadoDetails(
        nombre=texto(datos, "nombre"),
        apellido=texto(datos, "apellido"),
        ci=texto(datos, "ci"),
        restaurante_id=restaurante_id,
        salario=salario,
        fecha_ingreso=fecha_ingreso,
        correo=texto_opcional(datos, "correo"),
        telefono=texto_opcional(datos, "telefono"),
        direccion=texto_opcional(datos, "direccion"),
        activo=datos.get("activo") is True,
    )


# ------------------------------------------------------------------ lectura (pública)

@bp.route("/empleados", methods=["GET"])
def listar_empleados():
    return json_de(servicio().listar(privados=ve_datos_privados()))


@bp.route("/empleados/<int:empleado_id>", methods=["GET"])
def detalle_empleado(empleado_id):
    return json_de(servicio().obtener(empleado_id, privados=ve_datos_privados()))


# ------------------------------------------------------------------ escritura (solo admin)

@bp.route("/empleados", methods=["POST"])
@requires_auth("write:empleados")
def crear_empleado(payload):
    try:
        details = leer_empleado(cuerpo_json())
    except ValueError as err:
        return error_json("datos_invalidos", str(err), 400)
    return json_de(servicio().crear(details), 201)


@bp.route("/empleados/<int:empleado_id>", methods=["PUT"])
@requires_auth("write:empleados")
def editar_empleado(payload, empleado_id):
    try:
        details = leer_empleado(cuerpo_json())
    except ValueError as err:
        return error_json("datos_invalidos", str(err), 400)
    return json_de(servicio().actualizar(empleado_id, details))


@bp.route("/empleados/<int:empleado_id>", methods=["DELETE"])
@requires_auth("delete:empleados")
def eliminar_empleado(payload, empleado_id):
    servicio().eliminar(empleado_id)
    return "", 204
