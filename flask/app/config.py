import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://lacarta:lacarta@localhost:5432/lacarta",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 1 behind nginx: trust its X-Forwarded-Proto and Host headers.
    BEHIND_PROXY = os.environ.get("BEHIND_PROXY", "0") == "1"

    # Auth0. Flask only verifies tokens, so it needs no client secret.
    # The SPA client id is public: the frontend reads it from /api/config.
    AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "") # your-tenant.us.auth0.com
    AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE", "") # the API Identifier
    AUTH0_SPA_CLIENT_ID = os.environ.get("AUTH0_SPA_CLIENT_ID", "") # the Single Page Application

class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTH0_DOMAIN = "test-tenant.us.auth0.com"
    AUTH0_AUDIENCE = "lacarta-api"
    AUTH0_SPA_CLIENT_ID = "test-spa-client-id"
