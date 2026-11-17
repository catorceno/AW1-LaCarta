from app import create_app

# En producción, BEHIND_PROXY llega desde el entorno
# (docker-compose.prod.yml), así que ya no hace falta ProductionConfig.
app = create_app()