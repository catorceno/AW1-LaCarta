"""API de la carta: lee el JSON, llama al servicio y responde JSON.

Las reglas están en services/restaurante_service.py. Los errores del
dominio los traduce respuestas.registrar_errores.
"""
from flask import Blueprint, current_app, request

from .auth import requires_auth
from .extensions import db
from .repositories import RestauranteRepository
from .respuestas import cuerpo_json, decimal, error_json, json_de, texto, texto_opcional
from .services.restaurante_service import PlatoDetails, RestauranteDetails, RestauranteService

bp = Blueprint("carta", __name__, url_prefix="/api")


def servicio():
    return RestauranteService(RestauranteRepository(db.session))


def leer_restaurante(datos):
    return RestauranteDetails(
        nombre=texto(datos, "nombre"),
        ciudad=texto(datos, "ciudad"),
        direccion=texto_opcional(datos, "direccion"),
        telefono=texto_opcional(datos, "telefono"),
    )


@bp.route("/config", methods=["GET"])
def config_publica():
    """Lo que el frontend necesita para el login con el SDK de Auth0. Nada de esto es secreto."""
    return {
        "domain": current_app.config["AUTH0_DOMAIN"],
        "audience": current_app.config["AUTH0_AUDIENCE"],
        "client_id": current_app.config["AUTH0_SPA_CLIENT_ID"],
    }


@bp.route("/restaurantes", methods=["GET"])
def listar_restaurantes():
    ciudad = request.args.get("ciudad", "").strip()
    return json_de(servicio().listar(ciudad))


@bp.route("/restaurantes/<int:restaurante_id>", methods=["GET"])
def detalle_restaurante(restaurante_id):
    restaurante, platos = servicio().carta(restaurante_id)
    return json_de({"restaurante": restaurante, "platos": platos})


@bp.route("/restaurantes", methods=["POST"])
@requires_auth("write:carta")
def crear_restaurante(payload):
    return json_de(servicio().crear(leer_restaurante(cuerpo_json())), 201)


@bp.route("/restaurantes/<int:restaurante_id>", methods=["PUT"])
@requires_auth("write:carta")
def editar_restaurante(payload, restaurante_id):
    return json_de(servicio().actualizar(restaurante_id, leer_restaurante(cuerpo_json())))


@bp.route("/restaurantes/<int:restaurante_id>", methods=["DELETE"])
@requires_auth("delete:carta")
def eliminar_restaurante(payload, restaurante_id):
    servicio().eliminar(restaurante_id)
    return "", 204


@bp.route("/restaurantes/<int:restaurante_id>/platos", methods=["POST"])
@requires_auth("write:carta")
def crear_plato(payload, restaurante_id):
    datos = cuerpo_json()
    try:
        plato = PlatoDetails(
            nombre=texto(datos, "nombre"),
            precio=decimal(datos.get("precio"), "El precio debe ser un número."),
            disponible=datos.get("disponible") is True,
        )
    except ValueError as err:
        return error_json("datos_invalidos", str(err), 400)

    return json_de(servicio().agregar_plato(restaurante_id, plato), 201)
