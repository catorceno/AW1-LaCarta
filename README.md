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


## Qué quedó incompleto o qué haría distinto

### Problemas conocidos sin resolver

- **Errores 500 abruptos.** Algunas veces, al interactuar con la aplicación o al recargar una página, aparece un *Internal Server Error* genérico que corta el uso. Se vio sobre todo en `/auth/callback`, al volver de Auth0. No llegué a identificar la causa con certeza: una hipótesis es que se recargue o se vuelva atrás a la URL del callback, cuyo `code` es de un solo uso. Lo que haría es que cualquier fallo del callback termine en la página de error propia con un mensaje claro, en vez de la genérica.
- **Login automático con la sesión anterior.** A veces, al pulsar *Ingresar*, la aplicación entra directamente con la cuenta del último usuario (por ejemplo, el cliente) sin mostrar el formulario de Auth0. Auth0 mantiene su propia sesión en el navegador, aparte de la cookie de Flask: si esa sesión sigue abierta (por cerrar la pestaña sin pulsar *Cerrar sesión*, o porque el logout no llegó a `/v2/logout`), Auth0 reutiliza la sesión sin pedir credenciales. Una mejora sería ofrecer un botón "Ingresar con otra cuenta" que envíe `prompt=login` a Auth0 para forzar el formulario.

### Interfaz

- Faltan ajustes visuales: la posición de algunos botones, los íconos de la barra lateral (son emojis) y algunos textos que siguen en inglés (por ejemplo, la página de acceso denegado).
- Cuando un pedido es inválido (cantidad fuera de rango, plato no disponible), se muestra una página de error 400 con el motivo. Sería mejor volver a mostrar el formulario con el error junto al plato correspondiente, sin perder las cantidades ya escritas.
- Al intentar borrar un restaurante que tiene pedidos, la base lo impide (`PROTECT`) y el usuario solo ve "No se pudo eliminar.", sin la razón.
- Las fechas de los pedidos se muestran en UTC, no en la hora de Bolivia.
- La cola de la cocina no se actualiza sola: hay que recargar la página (las notificaciones en tiempo real estaban fuera de alcance).

### Puntos de mejora o pendientes

- **Avance de estado concurrente.** `cambiar_estado` lee el estado del pedido y luego lo escribe. Si dos personas de cocina pulsan "Avanzar" sobre el mismo pedido a la vez, las dos leen el mismo estado y escriben el mismo siguiente; no se salta un paso, pero tampoco se detecta el choque. Lo haría con una actualización condicional (`UPDATE … WHERE id = … AND estado = 'pendiente'`) y comprobando cuántas filas cambió.
- **Un solo `docker-compose.yml` para desarrollo y producción.** En el servidor, el contenedor de Flask también monta el código con un volumen e instala las dependencias de desarrollo (pytest). Funciona, pero lo correcto sería que en producción el código viva solo dentro de la imagen y sin herramientas de desarrollo.
- **Protección CSRF parcial.** Los formularios dependen de la cookie de sesión con `SameSite=Lax`, que bloquea los POST desde otros sitios, pero no hay tokens CSRF por formulario (por ejemplo, con Flask-WTF).
- **El cliente se guarda solo con su `sub`** (`auth0|…`). En el admin de Django no se ve quién es la persona; guardaría también su correo al crear el pedido para que el personal pueda buscarlo.
- **El admin de Django no valida las reglas de negocio** (por ejemplo, permite un ítem de otro restaurante). El enunciado lo permite porque es una herramienta interna, pero sería fácil repetir ahí la validación.
- **Sin respaldos de la base.** Los datos sobreviven a `docker compose down` gracias al volumen, pero no hay copias con `pg_dump`.
