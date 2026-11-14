"""Las seis pruebas obligatorias del examen (R6), más una matriz de rutas.

Cada prueba dice qué regla comprueba. Si se borra el decorador de una ruta
o la validación correspondiente, al menos una de estas pruebas falla.
"""
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import ItemPedido, Pedido
from tests.conftest import ADMIN, CLIENTE, COCINA, SUB_ANA, SUB_BETO


def contar(modelo):
    return db.session.scalar(db.select(db.func.count()).select_from(modelo))


def crear_pedido_en_bd(restaurante_id, plato, cliente=SUB_ANA, estado="pendiente"):
    """Un pedido escrito directamente en la base, para las pruebas que no lo crean por la web."""
    pedido = Pedido(cliente=cliente, restaurante_id=restaurante_id, estado=estado,
                    total=plato.precio)
    pedido.items.append(ItemPedido(plato_id=plato.id, cantidad=1, precio_unitario=plato.precio))
    db.session.add(pedido)
    db.session.commit()
    return pedido.id


# ------------------------------------------------------------ las seis obligatorias

def test_1_sin_sesion_crear_pedido_no_crea_nada(client, platos):
    """R6.1 · R2.5: sin sesión, crear un pedido responde 401 y no escribe nada."""
    silpancho = platos["Silpancho"]
    res = client.post(f"/restaurantes/{silpancho.restaurante_id}/pedidos",
                      data={f"cantidad-{silpancho.id}": "2"})

    assert res.status_code == 401
    assert "/auth/login" in res.get_data(as_text=True)                 # la página para ingresar
    assert contar(Pedido) == 0
    assert contar(ItemPedido) == 0


def test_2_cliente_no_puede_avanzar_el_estado(client, sign_in, platos):
    """R6.2 · R2.4: un cliente que envía el formulario de la cocina recibe 403."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)
    sign_in(CLIENTE)

    res = client.post(f"/cocina/pedidos/{pedido_id}/estado", data={"estado": "en_preparacion"})

    assert res.status_code == 403
    assert db.session.get(Pedido, pedido_id).estado == "pendiente"


def test_3_el_total_lo_calcula_el_servidor(client, sign_in, platos):
    """R6.3 · R1.3 · R1.4: un precio o total inventado en el formulario se ignora."""
    silpancho, sajta = platos["Silpancho"], platos["Sajta"]
    sign_in(CLIENTE)

    res = client.post(f"/restaurantes/{silpancho.restaurante_id}/pedidos", data={
        f"cantidad-{silpancho.id}": "2",
        f"cantidad-{sajta.id}": "1",
        f"precio-{silpancho.id}": "0.01",       # inventado: no debe usarse
        "total": "1.00",                        # inventado: no debe usarse
        "cliente": SUB_BETO,                    # inventado: el cliente sale del token
    })

    assert res.status_code == 302                                   # Post/Redirect/Get
    pedido = db.session.scalars(db.select(Pedido)).one()
    assert pedido.total == Decimal("81.00")                         # 2 × 25.50 + 1 × 30.00
    assert pedido.cliente == SUB_ANA
    precios = {item.plato_id: item.precio_unitario for item in pedido.items}
    assert precios == {silpancho.id: Decimal("25.50"), sajta.id: Decimal("30.00")}


def test_4_plato_no_disponible_rechaza_todo_el_pedido(client, sign_in, platos):
    """R6.4 · R1.5: un plato no disponible anula el pedido completo; no queda ninguna fila."""
    silpancho, lechon = platos["Silpancho"], platos["Lechón"]
    sign_in(CLIENTE)

    res = client.post(f"/restaurantes/{silpancho.restaurante_id}/pedidos", data={
        f"cantidad-{silpancho.id}": "1",        # este sí es válido...
        f"cantidad-{lechon.id}": "1",           # ...pero este no está disponible
    })

    assert res.status_code == 400
    assert contar(Pedido) == 0
    assert contar(ItemPedido) == 0


def test_5_pedido_de_otro_cliente_es_404(client, sign_in, platos):
    """R6.5 · R2.6: el pedido de otro cliente responde 404, no 403."""
    silpancho = platos["Silpancho"]
    pedido_de_beto = crear_pedido_en_bd(silpancho.restaurante_id, silpancho, cliente=SUB_BETO)
    sign_in(CLIENTE, sub=SUB_ANA)

    assert client.get(f"/pedidos/{pedido_de_beto}").status_code == 404
    assert client.post(f"/pedidos/{pedido_de_beto}/cancelar").status_code == 404
    assert db.session.get(Pedido, pedido_de_beto).estado == "pendiente"


def test_6_cocina_no_puede_volver_de_listo_a_pendiente(client, sign_in, platos):
    """R6.6 · tabla de estados: solo se avanza un paso; listo -> pendiente se rechaza."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho, estado="listo")
    sign_in(COCINA)

    res = client.post(f"/cocina/pedidos/{pedido_id}/estado", data={"estado": "pendiente"})

    assert res.status_code == 400
    assert db.session.get(Pedido, pedido_id).estado == "listo"


# ------------------------------------------------------------ más reglas de R1 y R2

def test_plato_de_otro_restaurante_rechaza_el_pedido(client, sign_in, platos):
    """R1.5: todos los platos tienen que ser del restaurante del pedido."""
    silpancho, pique = platos["Silpancho"], platos["Pique macho"]
    sign_in(CLIENTE)

    res = client.post(f"/restaurantes/{silpancho.restaurante_id}/pedidos", data={
        f"cantidad-{silpancho.id}": "1",
        f"cantidad-{pique.id}": "1",
    })

    assert res.status_code == 400
    assert contar(Pedido) == 0


@pytest.mark.parametrize("cantidad", ["0", "-1", "21", "dos", "1.5"])
def test_cantidad_fuera_de_rango_se_rechaza(client, sign_in, platos, cantidad):
    """R1.5: la cantidad es un entero entre 1 y 20 (0 solo, sin otros platos, es un pedido vacío)."""
    silpancho = platos["Silpancho"]
    sign_in(CLIENTE)

    res = client.post(f"/restaurantes/{silpancho.restaurante_id}/pedidos",
                      data={f"cantidad-{silpancho.id}": cantidad})

    assert res.status_code == 400
    assert contar(Pedido) == 0


def test_cliente_cancela_solo_si_esta_pendiente(client, sign_in, platos):
    """Tabla de estados: pendiente -> cancelado sí; en_preparacion -> cancelado no."""
    silpancho = platos["Silpancho"]
    pendiente = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)
    en_cocina = crear_pedido_en_bd(silpancho.restaurante_id, silpancho, estado="en_preparacion")
    sign_in(CLIENTE)

    assert client.post(f"/pedidos/{pendiente}/cancelar").status_code == 302
    assert db.session.get(Pedido, pendiente).estado == "cancelado"

    assert client.post(f"/pedidos/{en_cocina}/cancelar").status_code == 400
    assert db.session.get(Pedido, en_cocina).estado == "en_preparacion"


def test_cocina_avanza_un_paso(client, sign_in, platos):
    """Tabla de estados: pendiente -> en_preparacion, con Post/Redirect/Get."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)
    sign_in(COCINA)

    res = client.post(f"/cocina/pedidos/{pedido_id}/estado", data={"estado": "en_preparacion"})

    assert res.status_code == 302
    assert db.session.get(Pedido, pedido_id).estado == "en_preparacion"


def test_la_carta_es_publica(client, platos):
    """R2.3: el listado y el detalle no piden login."""
    assert client.get("/restaurantes").status_code == 200
    assert client.get(f"/restaurantes/{platos['Silpancho'].restaurante_id}").status_code == 200


# Cada ruta protegida: sin sesión 401; con un rol que no tiene el permiso, 403.
# Si alguien borra el decorador de una de estas rutas, su caso falla.
RUTAS_PROTEGIDAS = [
    ("post", "/restaurantes/1/pedidos", COCINA),         # create:pedidos
    ("get", "/pedidos", COCINA),                         # read:mis-pedidos
    ("get", "/pedidos/1", COCINA),                       # read:mis-pedidos
    ("post", "/pedidos/1/cancelar", COCINA),             # read:mis-pedidos
    ("get", "/cocina", CLIENTE),                         # read:pedidos
    ("post", "/cocina/pedidos/1/estado", CLIENTE),       # update:pedidos
    ("get", "/restaurantes/crear", CLIENTE),             # write:carta
    ("post", "/restaurantes/crear", CLIENTE),            # write:carta
    ("post", "/restaurantes/1/editar", CLIENTE),         # write:carta
    ("post", "/restaurantes/1/platos", CLIENTE),         # write:carta
    ("post", "/restaurantes/1/eliminar", COCINA),        # delete:carta
]


@pytest.mark.parametrize("metodo, url, permisos_sin_acceso", RUTAS_PROTEGIDAS)
def test_rutas_protegidas(client, sign_in, metodo, url, permisos_sin_acceso):
    """R2.4 · R2.5: 401 sin sesión, 403 con sesión pero sin el permiso."""
    assert getattr(client, metodo)(url).status_code == 401

    sign_in(permisos_sin_acceso)
    assert getattr(client, metodo)(url).status_code == 403


def test_admin_ve_la_cola_pero_no_avanza(client, sign_in, platos):
    """R2.2: admin tiene read:pedidos pero no update:pedidos."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)
    sign_in(ADMIN)

    pagina = client.get("/cocina")
    assert pagina.status_code == 200
    assert "Pasar a" not in pagina.get_data(as_text=True)          # el botón no se muestra...
    res = client.post(f"/cocina/pedidos/{pedido_id}/estado", data={"estado": "en_preparacion"})
    assert res.status_code == 403                                   # ...y la ruta lo rechaza igual
