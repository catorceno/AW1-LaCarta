## URLs públicas:

- https://carta.lacarta-camila.duckdns.org/
- https://admin.lacarta-camila.duckdns.org/admin/

## Cómo levantarlo desde cero

### Requisitos previos

- **Auth0**: un tenant con la API `La Carta API` (Identifier `lacarta-api`, RS256, *Enable RBAC* y *Add Permissions in the Access Token*), los seis permisos (`create:pedidos`, `read:mis-pedidos`, `read:pedidos`, `update:pedidos`, `write:carta`, `delete:carta`), los roles `cliente`, `cocina` y `admin`, y la Regular Web Application `La Carta Web` autorizada en *API Access*.
- **Para producción**: una instancia EC2 con Ubuntu, un Security Group que solo abra los puertos **22, 80 y 443**, y un dominio que apunte a su IP pública (aquí, `lacarta-camila.duckdns.org`; los subdominios `carta.` y `admin.` resuelven a la misma IP).

### En local (desarrollo)

Requiere Docker Desktop.

```bash
git clone https://github.com/catorceno/AW1-LaCarta.git
cd AW1-LaCarta
cp .env.example .env          # y completar los valores (ver la tabla de abajo)
docker compose up -d --build
docker compose ps             # migrate: Exited (0); db, django y flask: Up
docker compose exec flask flask seed                              # datos de prueba (opcional)
docker compose exec django python manage.py createsuperuser       # usuario del admin
```

- Carta (Flask): <http://localhost:5001> — tiene que ser `localhost`, no `127.0.0.1`, por las URLs registradas en Auth0.
- Admin (Django): <http://localhost:8000/admin/> — sin estilos en local: los estáticos los sirve Nginx en producción.
- Pruebas: `docker compose exec flask pytest -q`

En Auth0 (*La Carta Web → Settings*): Allowed Callback URLs `http://localhost:5001/auth/callback` y Allowed Logout URLs `http://localhost:5001/`.

### En producción (EC2 con Ubuntu)

**1. Instalar Docker, Nginx y Certbot**

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
exit      # volver a entrar por SSH para que el grupo docker tenga efecto
```

**2. Código y variables de entorno**

```bash
git clone https://github.com/catorceno/AW1-LaCarta.git
cd AW1-LaCarta
cp .env.example .env
nano .env
```

Claves nuevas para el servidor: `python3 -c "import secrets; print(secrets.token_hex(32))"`.

| Variable | Valor en producción |
|---|---|
| `POSTGRES_PASSWORD`, `FLASK_SECRET_KEY`, `DJANGO_SECRET_KEY` | Claves aleatorias generadas en el servidor |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_ALLOWED_HOSTS` | `admin.lacarta-camila.duckdns.org` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://admin.lacarta-camila.duckdns.org` |
| `BEHIND_PROXY` | `1` (Flask confía en los `X-Forwarded-*` de Nginx: ProxyFix) |
| `SESSION_COOKIE_SECURE` | `1` (la cookie de sesión solo viaja por HTTPS) |
| `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET` | Los de *La Carta Web* y *La Carta API* en Auth0 |

**3. Levantar los contenedores**

```bash
docker compose up -d --build
docker compose ps                            # migrate: Exited (0); db, django y flask: Up
docker compose logs migrate | tail           # migraciones aplicadas y collectstatic
docker compose exec django python manage.py createsuperuser
docker compose exec flask flask seed         # opcional: datos de prueba
```

**4. Nginx: los dos subdominios**

```bash
chmod o+x /home/ubuntu                       # Nginx (www-data) necesita atravesar la carpeta para leer los estáticos
sudo cp nginx/lacarta.conf /etc/nginx/sites-available/lacarta
sudo ln -s /etc/nginx/sites-available/lacarta /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

**5. HTTPS con Let's Encrypt**

```bash
sudo certbot --nginx -d carta.lacarta-camila.duckdns.org -d admin.lacarta-camila.duckdns.org
systemctl list-timers | grep certbot         # renovación automática (timer de systemd)
sudo certbot renew --dry-run                 # simula la renovación
```

Certbot agrega a `/etc/nginx/sites-available/lacarta` los bloques de 443 y la redirección de 80 a 443.

**6. Auth0**

En *La Carta Web → Settings*, agregar (sin borrar las de localhost):

- Allowed Callback URLs: `https://carta.lacarta-camila.duckdns.org/auth/callback`
- Allowed Logout URLs: `https://carta.lacarta-camila.duckdns.org/`

**7. Verificar**

```bash
curl -I http://carta.lacarta-camila.duckdns.org    # 301 hacia https://
sudo ss -tlnp                                      # 5001 y 8000 solo en 127.0.0.1; 5432 no aparece
```

### Actualizar el servidor después de un cambio

```bash
cd ~/AW1-LaCarta
git pull
docker compose up -d --build
```

`migrate` vuelve a correr y aplica las migraciones nuevas antes de que arranquen `django` y `flask`.
