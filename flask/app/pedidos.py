"""Presentación de pedidos: lee el formulario, llama al servicio y elige la plantilla.

Las reglas están en services/pedido_service.py. Los errores del dominio
(ReglaDeNegocioError -> 400, NoEncontradoError -> 404) los responden los
manejadores de routes.py.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .auth import requires_auth
from .errors import NoSeGuardoError
from .extensions import db
from .repositories import PedidoRepository, RestauranteRepository
from .services.pedido_service import LineaPedido, PedidoDetails, PedidoService

bp = Blueprint("pedidos", __name__)


def servicio():
    return PedidoService(PedidoRepository(db.session), RestauranteRepository(db.session))


def leer_lineas(form):
    """Solo cantidad-<plato_id> = <cantidad> (R1.4); cualquier otro campo se ignora."""
    lineas = []
    for clave, valor in form.items():
        if not clave.startswith("cantidad-"):
            continue                              # un "precio" o "total" inventado se ignora
        valor = valor.strip()
        if valor in ("", "0"):
            continue                              # plato no elegido
        try:
            lineas.append(LineaPedido(plato_id=int(clave.removeprefix("cantidad-")), cantidad=int(valor)))
        except ValueError:
            abort(400, description="La cantidad debe ser un número entero.")
    return tuple(lineas)


# ------------------------------------------------------------------ cliente

@bp.route("/restaurantes/<int:restaurante_id>/pedidos", methods=["POST"])
@requires_auth("create:pedidos")
def crear_pedido(payload, restaurante_id):
    details = PedidoDetails(restaurante_id=restaurante_id, lineas=leer_lineas(request.form))

    try:
        pedido_id = servicio().crear(payload["sub"], details)                # R1.2: el cliente sale del token
    except NoSeGuardoError:
        flash("No se pudo crear el pedido.", "error")
        return redirect(url_for("carta.detalle_restaurante", restaurante_id=restaurante_id))

    flash(f"Pedido #{pedido_id} creado.", "exito")
    return redirect(url_for("pedidos.detalle_pedido", pedido_id=pedido_id))   # Post/Redirect/Get


@bp.route("/pedidos", methods=["GET"])
@requires_auth("read:mis-pedidos")
def mis_pedidos(payload):
    return render_template("pedidos/index.html", pedidos=servicio().mis_pedidos(payload["sub"]))


@bp.route("/pedidos/<int:pedido_id>", methods=["GET"])
@requires_auth("read:mis-pedidos")
def detalle_pedido(payload, pedido_id):
    return render_template("pedidos/detalle.html", pedido=servicio().obtener_propio(pedido_id, payload["sub"]))


@bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@requires_auth("read:mis-pedidos")
def cancelar_pedido(payload, pedido_id):
    try:
        servicio().cancelar(pedido_id, payload["sub"])
        flash(f"Pedido #{pedido_id} cancelado.", "exito")
    except NoSeGuardoError:
        flash("No se pudo cancelar el pedido.", "error")

    return redirect(url_for("pedidos.detalle_pedido", pedido_id=pedido_id))


# ------------------------------------------------------------------ cocina

@bp.route("/cocina", methods=["GET"])
@requires_auth("read:pedidos")
def cocina(payload):
    return render_template("cocina/index.html", pedidos=servicio().cola_de_cocina())


@bp.route("/cocina/pedidos/<int:pedido_id>/estado", methods=["POST"])
@requires_auth("update:pedidos")
def cambiar_estado(payload, pedido_id):
    nuevo = request.form.get("estado", "").strip()

    try:
        etiqueta = servicio().avanzar(pedido_id, nuevo)
        flash(f"Pedido #{pedido_id}: {etiqueta}.", "exito")
    except NoSeGuardoError:
        flash("No se pudo cambiar el estado.", "error")

    return redirect(url_for("pedidos.cocina"))
