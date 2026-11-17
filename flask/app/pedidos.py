"""API de pedidos: lee el JSON, llama al servicio y responde JSON.

Las reglas están en services/pedido_service.py. Los errores del dominio
(ReglaDeNegocioError -> 400, NoEncontradoError -> 404) los traduce
respuestas.registrar_errores.
"""
from flask import Blueprint

from .auth import requires_auth
from .extensions import db
from .repositories import PedidoRepository, RestauranteRepository
from .respuestas import cuerpo_json, entero, error_json, json_de, texto
from .services.pedido_service import LineaPedido, PedidoDetails, PedidoService

bp = Blueprint("pedidos", __name__, url_prefix="/api")


def servicio():
    return PedidoService(PedidoRepository(db.session), RestauranteRepository(db.session))


def leer_lineas(datos):
    """Solo plato_id y cantidad de cada línea (R1.4); un "precio", "total" o "cliente" se ignora."""
    lineas = datos.get("lineas") or []
    if not isinstance(lineas, list):
        raise ValueError("lineas debe ser una lista.")
    resultado = []
    for linea in lineas:
        if not isinstance(linea, dict):
            raise ValueError("Cada línea debe tener plato_id y cantidad.")
        resultado.append(LineaPedido(
            plato_id=entero(linea.get("plato_id"), "plato_id debe ser un número entero."),
            cantidad=entero(linea.get("cantidad"), "La cantidad debe ser un número entero."),
        ))
    return tuple(resultado)


# ------------------------------------------------------------------ cliente

@bp.route("/restaurantes/<int:restaurante_id>/pedidos", methods=["POST"])
@requires_auth("create:pedidos")
def crear_pedido(payload, restaurante_id):
    try:
        details = PedidoDetails(restaurante_id=restaurante_id, lineas=leer_lineas(cuerpo_json()))
    except ValueError as err:
        return error_json("datos_invalidos", str(err), 400)

    s = servicio()
    pedido_id = s.crear(payload["sub"], details)                    # R1.2: el cliente sale del token
    return json_de(s.obtener_propio(pedido_id, payload["sub"]), 201)


@bp.route("/pedidos", methods=["GET"])
@requires_auth("read:mis-pedidos")
def mis_pedidos(payload):
    return json_de(servicio().mis_pedidos(payload["sub"]))


@bp.route("/pedidos/<int:pedido_id>", methods=["GET"])
@requires_auth("read:mis-pedidos")
def detalle_pedido(payload, pedido_id):
    return json_de(servicio().obtener_propio(pedido_id, payload["sub"]))


@bp.route("/pedidos/<int:pedido_id>", methods=["PATCH"])
@requires_auth("read:mis-pedidos")
def cancelar_pedido(payload, pedido_id):
    """El cliente solo puede pedir {"estado": "cancelado"}."""
    if texto(cuerpo_json(), "estado") != "cancelado":
        return error_json("datos_invalidos", 'Solo puedes cambiar tu pedido a "cancelado".', 400)
    return json_de(servicio().cancelar(pedido_id, payload["sub"]))


# ------------------------------------------------------------------ cocina

@bp.route("/cocina/pedidos", methods=["GET"])
@requires_auth("read:pedidos")
def cocina(payload):
    return json_de(servicio().cola_de_cocina())


@bp.route("/cocina/pedidos/<int:pedido_id>", methods=["PATCH"])
@requires_auth("update:pedidos")
def cambiar_estado(payload, pedido_id):
    """{"estado": "<siguiente>"}: solo se acepta el siguiente paso de la tabla."""
    return json_de(servicio().avanzar(pedido_id, texto(cuerpo_json(), "estado")))
