"""Las páginas del frontend: un HTML por pantalla, con las mismas URL de antes.

Flask solo entrega el archivo; cada página pide sus datos a /api/ con fetch.
Las páginas no exigen login: lo que protege los datos es @requires_auth en la API.
"""
from flask import Blueprint, current_app, redirect, send_from_directory

bp = Blueprint("paginas", __name__)

PAGINAS = [
    # (url, endpoint, archivo en static/paginas/)
    ("/restaurantes", "restaurantes", "restaurantes.html"),
    ("/restaurantes/crear", "crear_restaurante", "restaurante-formulario.html"),
    ("/restaurantes/<int:restaurante_id>", "restaurante", "restaurante.html"),
    ("/restaurantes/<int:restaurante_id>/editar", "editar_restaurante", "restaurante-formulario.html"),
    ("/pedidos", "pedidos", "pedidos.html"),
    ("/pedidos/<int:pedido_id>", "pedido", "pedido.html"),
    ("/cocina", "cocina", "cocina.html"),
    ("/empleados", "empleados", "empleados.html"),
    ("/empleados/crear", "crear_empleado", "empleado-formulario.html"),
    ("/empleados/<int:empleado_id>", "empleado", "empleado.html"),
    ("/empleados/<int:empleado_id>/editar", "editar_empleado", "empleado-formulario.html"),
    ("/callback", "callback", "callback.html"),   # Auth0 vuelve aquí después del login
]


def _servir(archivo):
    def vista(**_parametros):          # el id lo lee el JS de la página desde la URL
        return send_from_directory(current_app.static_folder, f"paginas/{archivo}")
    return vista


for url, endpoint, archivo in PAGINAS:
    bp.add_url_rule(url, endpoint, _servir(archivo), methods=["GET"])


@bp.route("/", methods=["GET"])
def inicio():
    return redirect("/restaurantes")
