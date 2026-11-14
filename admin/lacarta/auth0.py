"""Login del admin de Django con Auth0 (Authorization Code, como en Flask).

1. /admin/login/  -> redirige a la página de login de Auth0.
2. /auth/callback/ -> Authlib canjea el código por los tokens (servidor a servidor,
   con el client secret); el access token se verifica con las claves públicas de
   Auth0, igual que en Flask.
3. Si el token trae write:empleados (solo el rol admin), se crea o actualiza el
   usuario de Django ligado al `sub` y se inicia la sesión. Si no, 403.
4. /admin/logout/ -> cierra la sesión de Django y también la de Auth0.

No hay login con contraseña: los usuarios de Django no tienen una utilizable.
"""
from urllib.parse import urlencode

import jwt
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

# El permiso de Auth0 que da acceso al admin de Django. Solo lo tiene el rol admin.
PERMISO_ADMIN = "write:empleados"

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)

# Claves públicas de Auth0 (JWKS): se descargan una vez y quedan en memoria
_jwks = jwt.PyJWKClient(f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json",
                        cache_keys=True, timeout=5)


def verificar_access_token(token):
    """Mismas comprobaciones que verify_decode_jwt en Flask: firma RS256, exp, aud e iss."""
    clave = _jwks.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        clave.key,
        algorithms=["RS256"],
        audience=settings.AUTH0_AUDIENCE,
        issuer=f"https://{settings.AUTH0_DOMAIN}/",
        options={"require": ["exp", "iat", "sub"]},
    )


def sin_acceso(request, mensaje, status=403):
    return render(request, "auth0/sin_acceso.html", {"mensaje": mensaje}, status=status)


def iniciar_sesion(request):
    """Guarda a dónde volver y envía el navegador a Auth0."""
    siguiente = request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
        siguiente = reverse("admin:index")                    # sin open redirect
    request.session["auth0_next"] = siguiente

    return oauth.auth0.authorize_redirect(
        request,
        request.build_absolute_uri(reverse("auth0_callback")),
        audience=settings.AUTH0_AUDIENCE,                    # para que el token traiga los permisos
    )


def callback(request):
    """Auth0 vuelve aquí con el código de un solo uso."""
    try:
        token = oauth.auth0.authorize_access_token(request)
        payload = verificar_access_token(token["access_token"])
    except OAuthError as err:
        return sin_acceso(request, f"Auth0: {err.description or err.error}", status=400)
    except jwt.PyJWTError:
        return sin_acceso(request, "El token de Auth0 no es válido.", status=401)

    if PERMISO_ADMIN not in payload.get("permissions", []):
        return sin_acceso(request, "Tu cuenta no tiene el rol admin: no puede entrar al admin de Django.")

    # El usuario de Django queda ligado al sub de Auth0. El rol se revisa en cada login:
    # si en Auth0 le quitan el rol admin, la próxima vez ya no entra.
    perfil = token.get("userinfo") or {}
    usuario, _ = get_user_model().objects.get_or_create(username=payload["sub"])
    usuario.email = perfil.get("email") or ""
    usuario.first_name = (perfil.get("name") or "")[:150]
    usuario.is_staff = True              # puede entrar al admin
    usuario.is_superuser = True          # y administrar todos los modelos
    usuario.set_unusable_password()      # sin login con contraseña
    usuario.save()

    siguiente = request.session.pop("auth0_next", reverse("admin:index"))
    login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
    return redirect(siguiente)


@require_POST
def cerrar_sesion(request):
    """Cierra la sesión de Django y después la de Auth0 (si no, Ingresar volvería a entrar solo)."""
    logout(request)
    params = urlencode({
        "returnTo": request.build_absolute_uri(reverse("admin:index")),
        "client_id": settings.AUTH0_CLIENT_ID,
    })
    return redirect(f"https://{settings.AUTH0_DOMAIN}/v2/logout?{params}")