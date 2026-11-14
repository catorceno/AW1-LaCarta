"""Fixtures de las pruebas: Flask sin Auth0 de verdad y sin Postgres.

- La base es SQLite en memoria, creada con create_all() a partir de los
  modelos de Flask (en producción las tablas las crea Django; aquí no hay
  Django, así que las pruebas crean una base vacía con las mismas columnas
  y los mismos CHECK).
- No se llama a Auth0: se genera aquí un par de claves RSA, el cliente de
  claves de la app recibe la mitad pública en el formato del JWKS de Auth0,
  y los tokens se firman con la mitad privada. verify_decode_jwt corre el
  mismo código que en producción.
- sign_in() escribe el token en la sesión, igual que /auth/callback.
"""
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Plato, Restaurante

KID = "test-key-1"
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)

CLIENTE = ["create:pedidos", "read:mis-pedidos"]
COCINA = ["read:pedidos", "update:pedidos"]
ADMIN = ["read:pedidos", "write:carta", "delete:carta"]

SUB_ANA = "auth0|ana"
SUB_BETO = "auth0|beto"


class PruebasConfig(TestConfig):
    # Por si el .env del contenedor trae los valores de producción:
    # en las pruebas el cliente habla http://localhost, sin proxy.
    SESSION_COOKIE_SECURE = False
    BEHIND_PROXY = False


def jwks():
    """La mitad pública, con el formato con que Auth0 publica sus claves."""
    key = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(PRIVATE_KEY.public_key()))
    return {"keys": [{**key, "kid": KID, "use": "sig", "alg": "RS256"}]}


@pytest.fixture
def app():
    app = create_app(PruebasConfig)
    app.extensions["auth0_jwks"].fetch_data = jwks      # no descarga nada de Auth0

    with app.app_context():
        db.create_all()

        # Restaurante 1 con dos platos disponibles y uno no disponible,
        # y Restaurante 2 con un plato propio (para "plato de otro restaurante").
        r1 = Restaurante(nombre="La Cumbre", ciudad="La Paz")
        r1.platos = [
            Plato(nombre="Silpancho", precio=Decimal("25.50"), disponible=True),
            Plato(nombre="Sajta", precio=Decimal("30.00"), disponible=True),
            Plato(nombre="Lechón", precio=Decimal("40.00"), disponible=False),
        ]
        r2 = Restaurante(nombre="El Valle", ciudad="Cochabamba")
        r2.platos = [Plato(nombre="Pique macho", precio=Decimal("45.00"), disponible=True)]
        db.session.add_all([r1, r2])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_token(app):
    """Firma un token con la forma de un access token de Auth0."""
    def _make(permissions, sub=SUB_ANA):
        now = datetime.now(timezone.utc)
        payload = {
            "iss": f"https://{app.config['AUTH0_DOMAIN']}/",
            "sub": sub,
            "aud": app.config["AUTH0_AUDIENCE"],
            "iat": now,
            "exp": now + timedelta(hours=1),
            "permissions": permissions,
        }
        return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256", headers={"kid": KID})
    return _make


@pytest.fixture
def sign_in(client, make_token):
    """Pone el token en la sesión, como lo hace /auth/callback después del login."""
    def _sign_in(permissions, sub=SUB_ANA):
        with client.session_transaction() as session:
            session["access_token"] = make_token(permissions, sub)
            session["user"] = {"name": sub, "email": f"{sub}@example.com"}
    return _sign_in


@pytest.fixture
def platos(app):
    """Los platos de la base de prueba, por nombre."""
    return {p.nombre: p for p in db.session.scalars(db.select(Plato))}
