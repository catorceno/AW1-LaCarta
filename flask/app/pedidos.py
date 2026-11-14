"""Pedidos: el cliente arma y cancela los suyos; la cocina avanza la cola.

Cada regla del enunciado se aplica aquí, en el servidor, antes del commit:
ocultar botones en las plantillas es solo comodidad.
"""
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.orm import joinedload, selectinload

from .auth import requires_auth
from .extensions import db
from .models import ETIQUETAS_ESTADO, ItemPedido, Pedido, Plato, Restaurante

bp = Blueprint("pedidos", __name__)

CANTIDAD_MAXIMA = 20

# La tabla de estados del enunciado. La cocina solo avanza un paso hacia
# adelante; cualquier otra transición se rechaza (por ejemplo, listo -> pendiente).
SIGUIENTE_ESTADO = {
    "pendiente": "en_preparacion",
    "en_preparacion": "listo",
    "listo": "entregado",
}
ESTADOS_ACTIVOS = tuple(SIGUIENTE_ESTADO)   # los que ve la cocina


def pedido_propio_o_404(pedido_id, sub):
    """El pedido si es de este cliente; si no existe o es de otro, 404.

    404 y no 403: un 403 confirmaría que ese pedido existe (R2.6).
    """
    return db.first_or_404(
        db.select(Pedido)
        .options(joinedload(Pedido.restaurante), selectinload(Pedido.items).joinedload(ItemPedido.plato))
        .filter_by(id=pedido_id, cliente=sub)
    )


# ------------------------------------------------------------------ cliente

@bp.route("/restaurantes/<int:restaurante_id>/pedidos", methods=["POST"])
@requires_auth("create:pedidos")
def crear_pedido(payload, restaurante_id):
    """Crea un pedido con todos sus ítems, o no crea nada (R1).

    El formulario solo trae cantidad-<plato_id> = <cantidad>. El cliente, los
    precios y el total los pone el servidor: nunca se leen del formulario.
    """
    restaurante = db.get_or_404(Restaurante, restaurante_id)

    # 1. Leer el formulario: solo plato y cantidad (R1.4)
    lineas = []                                   # [(plato_id, cantidad), ...]
    for clave, valor in request.form.items():
        if not clave.startswith("cantidad-"):
            continue                              # cualquier otro campo (un "precio" inventado) se ignora
        valor = valor.strip()
        if valor in ("", "0"):
            continue                              # plato no elegido
        try:
            plato_id = int(clave.removeprefix("cantidad-"))
            cantidad = int(valor)
        except ValueError:
            abort(400, description="La cantidad debe ser un número entero.")
        if not 1 <= cantidad <= CANTIDAD_MAXIMA:
            abort(400, description=f"La cantidad debe estar entre 1 y {CANTIDAD_MAXIMA}.")
        lineas.append((plato_id, cantidad))

    if not lineas:
        abort(400, description="Elige al menos un plato.")

    # 2. Validar cada plato antes de escribir nada (R1.5)
    ids = [plato_id for plato_id, _ in lineas]
    platos = {p.id: p for p in db.session.scalars(db.select(Plato).where(Plato.id.in_(ids)))}

    for plato_id, _ in lineas:
        plato = platos.get(plato_id)
        if plato is None:
            abort(404)                                                        # R1.7
        if plato.restaurante_id != restaurante.id:
            abort(400, description=f"{plato.nombre} es de otro restaurante.")
        if not plato.disponible:
            abort(400, description=f"{plato.nombre} no está disponible.")

    # 3. Armar el pedido: cliente desde el token, precio congelado, total en el servidor
    pedido = Pedido(cliente=payload["sub"], restaurante_id=restaurante.id)   # R1.2
    total = Decimal("0")
    for plato_id, cantidad in lineas:
        plato = platos[plato_id]
        pedido.items.append(ItemPedido(
            plato_id=plato.id,
            cantidad=cantidad,
            precio_unitario=plato.precio,         # copia del precio de hoy (R1.3)
        ))
        total += plato.precio * cantidad
    pedido.total = total                          # R1.4

    # 4. Un solo commit: el pedido y todos sus ítems, o nada (R1.5)
    try:
        db.session.add(pedido)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("No se pudo crear el pedido.", "error")
        return redirect(url_for("carta.detalle_restaurante", restaurante_id=restaurante.id))

    flash(f"Pedido #{pedido.id} creado.", "exito")
    return redirect(url_for("pedidos.detalle_pedido", pedido_id=pedido.id))   # Post/Redirect/Get


@bp.route("/pedidos", methods=["GET"])
@requires_auth("read:mis-pedidos")
def mis_pedidos(payload):
    pedidos = db.session.scalars(
        db.select(Pedido)
        .options(joinedload(Pedido.restaurante))
        .filter_by(cliente=payload["sub"])                     # solo los propios
        .order_by(Pedido.fecha.desc())
    ).all()
    return render_template("pedidos/index.html", pedidos=pedidos)


@bp.route("/pedidos/<int:pedido_id>", methods=["GET"])
@requires_auth("read:mis-pedidos")
def detalle_pedido(payload, pedido_id):
    pedido = pedido_propio_o_404(pedido_id, payload["sub"])
    return render_template("pedidos/detalle.html", pedido=pedido)


@bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@requires_auth("read:mis-pedidos")
def cancelar_pedido(payload, pedido_id):
    """pendiente -> cancelado, solo el dueño del pedido."""
    pedido = pedido_propio_o_404(pedido_id, payload["sub"])

    if pedido.estado != "pendiente":
        abort(400, description="Solo se puede cancelar un pedido pendiente.")

    try:
        pedido.estado = "cancelado"
        db.session.commit()
        flash(f"Pedido #{pedido.id} cancelado.", "exito")
    except Exception:
        db.session.rollback()
        flash("No se pudo cancelar el pedido.", "error")

    return redirect(url_for("pedidos.detalle_pedido", pedido_id=pedido.id))


# ------------------------------------------------------------------ cocina

@bp.route("/cocina", methods=["GET"])
@requires_auth("read:pedidos")
def cocina(payload):
    pedidos = db.session.scalars(
        db.select(Pedido)
        .options(joinedload(Pedido.restaurante), selectinload(Pedido.items).joinedload(ItemPedido.plato))
        .where(Pedido.estado.in_(ESTADOS_ACTIVOS))
        .order_by(Pedido.fecha)                                # el más antiguo primero
    ).all()
    return render_template("cocina/index.html", pedidos=pedidos, siguiente=SIGUIENTE_ESTADO, etiquetas=ETIQUETAS_ESTADO)


@bp.route("/cocina/pedidos/<int:pedido_id>/estado", methods=["POST"])
@requires_auth("update:pedidos")
def cambiar_estado(payload, pedido_id):
    """La cocina pide pasar el pedido a `estado`; solo se acepta el siguiente paso."""
    pedido = db.get_or_404(Pedido, pedido_id)
    nuevo = request.form.get("estado", "").strip()

    if SIGUIENTE_ESTADO.get(pedido.estado) != nuevo:
        abort(400, description=f"No se puede pasar de {pedido.estado} a {nuevo or '(vacío)'}.")

    try:
        pedido.estado = nuevo
        db.session.commit()
        flash(f"Pedido #{pedido.id}: {pedido.estado_etiqueta}.", "exito")
    except Exception:
        db.session.rollback()
        flash("No se pudo cambiar el estado.", "error")

    return redirect(url_for("pedidos.cocina"))