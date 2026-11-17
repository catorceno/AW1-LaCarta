from functools import wraps

from flask import request

from .errors import AuthError
from .tokens import verify_decode_jwt


def get_token_auth_header():
    """Return the access token from `Authorization: Bearer <token>`.

    The frontend logs in with the Auth0 SPA SDK and sends the token in this
    header on every fetch, as in the course.
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description": "Authorization header is expected."}, 401)

    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                         "description": "Authorization header must start with \"Bearer\"."}, 401)
    if len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found."}, 401)
    if len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                         "description": "Authorization header must be bearer token."}, 401)

    return parts[1]


def check_permissions(permission, payload):
    if "permissions" not in payload:
        raise AuthError({"code": "invalid_claims", "description": "Permissions not included in the token."}, 400)

    if permission and permission not in payload["permissions"]:
        raise AuthError({"code": "forbidden", "description": "You do not have permission to do this."}, 403)

    return True


def requires_auth(permission=""):
    """Decorator factory: `@requires_auth('delete:carta')`.

    Three filters, in order: is there a token (401), is it valid (401),
    does it carry the permission (403). The decoded payload is passed to the
    view as its first argument, exactly like the course example.
    """

    def requires_auth_decorator(f):

        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator


def optional_payload():
    """The payload if the request carries a token, or None if it carries none.

    For public routes that show more to some users (the private data of an
    employee). A token that is present but invalid is still a 401: the
    frontend should know its session expired instead of silently seeing less.
    """
    if "Authorization" not in request.headers:
        return None
    return verify_decode_jwt(get_token_auth_header())
