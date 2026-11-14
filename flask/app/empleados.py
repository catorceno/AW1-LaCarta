"""Empleados: lista pública; crear, editar y borrar solo con los permisos de Auth0.

- Sin sesión, o con los roles cliente y cocina: solo lectura, y solo los
  datos públicos (nombre, apellido, restaurante, activo).
- write:empleados: crear, editar y ver los datos privados (CI, salario, contacto).
- delete:empleados: borrar.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from .auth import requires_auth
from .extensions import db
from .models import Empleado, Restaurante

bp = Blueprint("empleados", __name__)


def restaurantes_ordenados():
    return db.session.scalars(db.select(Restaurante).order_by(Restaurante.nombre)).all()


def leer_formulario(form):
    """Valida el formulario y devuelve los datos limpios, o lanza ValueError con el motivo."""
    nombre = form.get("nombre", "").strip()
    apellido = form.get("apellido", "").strip()
    ci = form.get("ci", "").strip()
    if not nombre or not apellido or not ci:
        raise ValueError("Nombre, apellido y C.I. son obligatorios.")
    if len(ci) > 12:
        raise ValueError("El C.I. tiene como máximo 12 caracteres.")

    try:
        restaurante_id = int(form.get("restaurante_id", ""))
    except ValueError:
        raise ValueError("Elige un restaurante.")
    if db.session.get(Restaurante, restaurante_id) is None:
        raise ValueError("El restaurante elegido no existe.")

    try:
        salario = Decimal(form.get("salario", "").strip())
    except InvalidOperation:
        raise ValueError("El salario debe ser un número.")
    if salario < 0:
        raise ValueError("El salario no puede ser negativo.")

    texto_fecha = form.get("fecha_ingreso", "").strip()
    try:
        fecha_ingreso = date.fromisoformat(texto_fecha) if texto_fecha else None
    except ValueError:
        raise ValueError("La fecha de ingreso no es válida.")

    return {
        "nombre": nombre,
        "apellido": apellido,
        "ci": ci,
        "restaurante_id": restaurante_id,
        "salario": salario,
        "fecha_ingreso": fecha_ingreso,               # None: la pone Postgres (db_default)
        "correo": form.get("correo", "").strip() or None,
        "telefono": form.get("telefono", "").strip() or None,
        "direccion": form.get("direccion", "").strip() or None,
        "activo": "activo" in form,                   # un checkbox sin marcar no se envía
    }


def volver_al_formulario(mensaje, empleado=None):
    """Muestra el formulario otra vez con el error y lo que el usuario ya había escrito."""
    flash(mensaje, "error")
    return render_template("empleados/formulario.html", empleado=empleado,
                           datos=request.form, restaurantes=restaurantes_ordenados()), 400


# ------------------------------------------------------------------ lectura (pública)

@bp.route("/empleados", methods=["GET"])
def listar_empleados():
    empleados = db.session.scalars(
        db.select(Empleado)
        .options(joinedload(Empleado.restaurante))
        .order_by(Empleado.apellido, Empleado.nombre)
    ).all()
    return render_template("empleados/index.html", empleados=empleados)


@bp.route("/empleados/<int:empleado_id>", methods=["GET"])
def detalle_empleado(empleado_id):
    # Los datos privados solo se muestran a quien tiene write:empleados (lo decide la plantilla)
    empleado = db.get_or_404(Empleado, empleado_id)
    return render_template("empleados/detalle.html", empleado=empleado)


# ------------------------------------------------------------------ escritura (solo admin)

@bp.route("/empleados/crear", methods=["GET"])
@requires_auth("write:empleados")
def formulario_crear_empleado(payload):
    return render_template("empleados/formulario.html", empleado=None, datos={},
                           restaurantes=restaurantes_ordenados())


@bp.route("/empleados/crear", methods=["POST"])
@requires_auth("write:empleados")
def crear_empleado(payload):
    try:
        datos = leer_formulario(request.form)
    except ValueError as err:
        return volver_al_formulario(str(err))

    if datos["fecha_ingreso"] is None:
        del datos["fecha_ingreso"]                    # sin la columna en el INSERT: Postgres pone la fecha de hoy
    empleado = Empleado(**datos)

    try:
        db.session.add(empleado)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return volver_al_formulario("Ya existe un empleado con ese C.I.")
    except Exception:
        db.session.rollback()
        flash("No se pudo crear el empleado.", "error")
        return redirect(url_for("empleados.listar_empleados"))

    flash(f"Empleado {empleado.nombre} {empleado.apellido} creado.", "exito")
    return redirect(url_for("empleados.detalle_empleado", empleado_id=empleado.id))


@bp.route("/empleados/<int:empleado_id>/editar", methods=["GET", "POST"])
@requires_auth("write:empleados")
def editar_empleado(payload, empleado_id):
    empleado = db.get_or_404(Empleado, empleado_id)

    if request.method == "GET":
        return render_template("empleados/formulario.html", empleado=empleado, datos={},
                               restaurantes=restaurantes_ordenados())

    try:
        datos = leer_formulario(request.form)
    except ValueError as err:
        return volver_al_formulario(str(err), empleado)

    if datos["fecha_ingreso"] is None:
        del datos["fecha_ingreso"]                    # vacía al editar: se mantiene la que tenía
    for campo, valor in datos.items():
        setattr(empleado, campo, valor)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return volver_al_formulario("Ya existe un empleado con ese C.I.", empleado)
    except Exception:
        db.session.rollback()
        flash("No se pudo actualizar el empleado.", "error")
        return redirect(url_for("empleados.detalle_empleado", empleado_id=empleado_id))

    flash("Empleado actualizado.", "exito")
    return redirect(url_for("empleados.detalle_empleado", empleado_id=empleado_id))


@bp.route("/empleados/<int:empleado_id>/eliminar", methods=["POST"])
@requires_auth("delete:empleados")
def eliminar_empleado(payload, empleado_id):
    empleado = db.get_or_404(Empleado, empleado_id)

    try:
        db.session.delete(empleado)
        db.session.commit()
        flash("Empleado eliminado.", "exito")
    except Exception:
        db.session.rollback()
        flash("No se pudo eliminar el empleado.", "error")

    return redirect(url_for("empleados.listar_empleados"))