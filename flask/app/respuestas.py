"""Presentación JSON: cómo se escriben las respuestas y los errores de la API.

Todos los errores tienen la misma forma que los de Auth0:
{"code": "...", "description": "..."}
"""
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import abort, current_app, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .errors import ConflictoError, NoEncontradoError, NoSeGuardoError, ReglaDeNegocioError
from .extensions import db


# ------------------------------------------------------------------ salida


def a_json(valor):
    """Un View (dataclass) a tipos de JSON: Decimal como texto ("25.50"), fechas en ISO 8601."""
    if is_dataclass(valor):
        valor = asdict(valor)
    if isinstance(valor, dict):
        return {k: a_json(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [a_json(v) for v in valor]
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def json_de(valor, status=200):
    return jsonify(a_json(valor)), status


def error_json(code, description, status):
    return jsonify({"code": code, "description": description}), status


# ------------------------------------------------------------------ entrada


def cuerpo_json():
    """El cuerpo de la petición como dict; 400 si no es un objeto JSON."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400, description="Se esperaba un objeto JSON.")
    return datos


def texto(datos, campo):
    """El texto del campo sin espacios a los costados ('' si no vino)."""
    valor = datos.get(campo)
    return "" if valor is None else str(valor).strip()


def texto_opcional(datos, campo):
    return texto(datos, campo) or None


def entero(valor, mensaje):
    """Un entero (o un texto con un entero); ValueError con `mensaje` si no lo es."""
    if isinstance(valor, bool) or not isinstance(valor, (int, str)):
        raise ValueError(mensaje)
    try:
        return int(valor)
    except ValueError:
        raise ValueError(mensaje)


def decimal(valor, mensaje):
    """Un número exacto (Decimal) a partir de un número o un texto JSON."""
    if isinstance(valor, bool) or valor is None:
        raise ValueError(mensaje)
    try:
        numero = Decimal(str(valor).strip())
    except InvalidOperation:
        raise ValueError(mensaje)
    if not numero.is_finite():
        raise ValueError(mensaje)
    return numero


# ------------------------------------------------------------------ errores


def registrar_errores(app):
    """Traduce los errores del dominio y de HTTP a respuestas.

    Bajo /api/ todo es JSON. Fuera de /api/ (las páginas), un 404 devuelve la
    página 404.html del frontend.
    """

    @app.errorhandler(ReglaDeNegocioError)
    def regla_rota(error):
        return error_json("regla_de_negocio", str(error), 400)

    @app.errorhandler(NoEncontradoError)
    def no_encontrado(error):
        return error_json("no_encontrado", str(error) or "No encontrado.", 404)

    @app.errorhandler(ConflictoError)
    def conflicto(error):
        return error_json("conflicto", "No se pudo guardar: entra en conflicto con otros datos "
                                       "(por ejemplo, tiene pedidos o empleados asociados).", 409)

    @app.errorhandler(NoSeGuardoError)
    def no_se_guardo(error):
        return error_json("no_se_guardo", "No se pudo guardar. Intenta de nuevo.", 500)

    @app.errorhandler(HTTPException)
    def error_http(error):
        if error.code == 404 and not request.path.startswith("/api/"):
            return send_from_directory(current_app.static_folder, "paginas/404.html"), 404
        codigo = (error.name or "error").lower().replace(" ", "_")
        return error_json(codigo, error.description, error.code)

    @app.errorhandler(500)
    def error_interno(error):
        db.session.rollback()
        return error_json("error_interno", "Ocurrió un error interno. Intenta de nuevo en un momento.", 500)
