"""Presentación de empleados: lista pública; crear, editar y borrar solo con los permisos de Auth0.

- Sin sesión, o con los roles cliente y cocina: solo lectura, y solo los
  datos públicos (nombre, apellido, restaurante, activo).
- write:empleados: crear, editar y ver los datos privados (CI, salario, contacto).
- delete:empleados: borrar.

Las reglas de los datos están en services/empleado_service.py.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import requires_auth
from .errors import NoSeGuardoError, ReglaDeNegocioError
from .extensions import db
from .repositories import EmpleadoRepository, RestauranteRepository
from .services.empleado_service import EmpleadoDetails, EmpleadoService

bp = Blueprint("empleados", __name__)


def servicio():
    return EmpleadoService(EmpleadoRepository(db.session), RestauranteRepository(db.session))


def leer_formulario(form):
    """Convierte el texto del formulario a un EmpleadoDetails, o lanza ValueError con el motivo.

    Aquí solo se revisa el formato; las reglas (obligatorios, C.I., salario,
    restaurante) las revisa el servicio.
    """
    try:
        restaurante_id = int(form.get("restaurante_id", ""))
    except ValueError:
        raise ValueError("Elige un restaurante.")

    try:
        salario = Decimal(form.get("salario", "").strip())
    except InvalidOperation:
        raise ValueError("El salario debe ser un número.")

    texto_fecha = form.get("fecha_ingreso", "").strip()
    try:
        fecha_ingreso = date.fromisoformat(texto_fecha) if texto_fecha else None
    except ValueError:
        raise ValueError("La fecha de ingreso no es válida.")

    return EmpleadoDetails(
        nombre=form.get("nombre", "").strip(),
        apellido=form.get("apellido", "").strip(),
        ci=form.get("ci", "").strip(),
        restaurante_id=restaurante_id,
        salario=salario,
        fecha_ingreso=fecha_ingreso,
        correo=form.get("correo", "").strip() or None,
        telefono=form.get("telefono", "").strip() or None,
        direccion=form.get("direccion", "").strip() or None,
        activo="activo" in form,                      # un checkbox sin marcar no se envía
    )


def volver_al_formulario(mensaje, empleado=None):
    """Muestra el formulario otra vez con el error y lo que el usuario ya había escrito."""
    flash(mensaje, "error")
    return render_template("empleados/formulario.html", empleado=empleado,
                           datos=request.form, restaurantes=servicio().restaurantes_para_elegir()), 400


# ------------------------------------------------------------------ lectura (pública)

@bp.route("/empleados", methods=["GET"])
def listar_empleados():
    return render_template("empleados/index.html", empleados=servicio().listar())


@bp.route("/empleados/<int:empleado_id>", methods=["GET"])
def detalle_empleado(empleado_id):
    # Los datos privados solo se muestran a quien tiene write:empleados (lo decide la plantilla)
    return render_template("empleados/detalle.html", empleado=servicio().obtener(empleado_id))


# ------------------------------------------------------------------ escritura (solo admin)

@bp.route("/empleados/crear", methods=["GET"])
@requires_auth("write:empleados")
def formulario_crear_empleado(payload):
    return render_template("empleados/formulario.html", empleado=None, datos={},
                           restaurantes=servicio().restaurantes_para_elegir())


@bp.route("/empleados/crear", methods=["POST"])
@requires_auth("write:empleados")
def crear_empleado(payload):
    try:
        empleado = servicio().crear(leer_formulario(request.form))
    except (ValueError, ReglaDeNegocioError) as err:
        return volver_al_formulario(str(err))
    except NoSeGuardoError:
        flash("No se pudo crear el empleado.", "error")
        return redirect(url_for("empleados.listar_empleados"))

    flash(f"Empleado {empleado.nombre} {empleado.apellido} creado.", "exito")
    return redirect(url_for("empleados.detalle_empleado", empleado_id=empleado.id))


@bp.route("/empleados/<int:empleado_id>/editar", methods=["GET", "POST"])
@requires_auth("write:empleados")
def editar_empleado(payload, empleado_id):
    if request.method == "GET":
        return render_template("empleados/formulario.html", empleado=servicio().obtener(empleado_id),
                               datos={}, restaurantes=servicio().restaurantes_para_elegir())

    try:
        servicio().actualizar(empleado_id, leer_formulario(request.form))
    except (ValueError, ReglaDeNegocioError) as err:
        return volver_al_formulario(str(err), servicio().obtener(empleado_id))
    except NoSeGuardoError:
        flash("No se pudo actualizar el empleado.", "error")
        return redirect(url_for("empleados.detalle_empleado", empleado_id=empleado_id))

    flash("Empleado actualizado.", "exito")
    return redirect(url_for("empleados.detalle_empleado", empleado_id=empleado_id))


@bp.route("/empleados/<int:empleado_id>/eliminar", methods=["POST"])
@requires_auth("delete:empleados")
def eliminar_empleado(payload, empleado_id):
    try:
        servicio().eliminar(empleado_id)
        flash("Empleado eliminado.", "exito")
    except NoSeGuardoError:
        flash("No se pudo eliminar el empleado.", "error")

    return redirect(url_for("empleados.listar_empleados"))
