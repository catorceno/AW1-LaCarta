from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
from .extensions import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    for key in ("AUTH0_DOMAIN", "AUTH0_AUDIENCE", "AUTH0_SPA_CLIENT_ID"):
        if not app.config[key]:
            raise RuntimeError(f"{key} is not set. Copy .env.example to .env and fill in your Auth0 values.")

    if app.config["BEHIND_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)

    from . import models # noqa: F401 carga los modelos que usan las tablas de Django
    from .auth import AuthError
    from .auth.handlers import handle_auth_error
    from .auth.tokens import jwks_client
    from .commands import seed
    from .respuestas import registrar_errores
    from .paginas import bp as paginas_bp
    from .routes import bp as carta_bp
    from .pedidos import bp as pedidos_bp
    from .empleados import bp as empleados_bp

    # One key client per app, so its cache lives as long as the process.
    app.extensions["auth0_jwks"] = jwks_client(app.config["AUTH0_DOMAIN"])

    app.register_blueprint(paginas_bp)      # el frontend: un HTML por pantalla
    app.register_blueprint(carta_bp)        # la API JSON, bajo /api/
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(empleados_bp)

    app.register_error_handler(AuthError, handle_auth_error)
    registrar_errores(app)

    app.cli.add_command(seed)

    return app
