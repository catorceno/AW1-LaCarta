from flask import jsonify

from .errors import AuthError


def handle_auth_error(err: AuthError):
    """401, 403 and 400 as JSON: {"code": ..., "description": ...}.

    The frontend decides what to show (the "Ingresar" button on a 401, the
    access-denied message on a 403).
    """
    return jsonify(err.error), err.status_code
