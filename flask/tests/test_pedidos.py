"""Las seis pruebas obligatorias del examen (R6), más una matriz de rutas.

Cada prueba dice qué regla comprueba. Si se borra el decorador de una ruta
o la validación correspondiente, al menos una de estas pruebas falla.
La API responde JSON; el token viaja en Authorization: Bearer.
"""
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import ItemPedido, Pedido
from tests.conftest import ADMIN, CLIENTE, COCINA, SUB_ANA, SUB_BETO


def contar(modelo):
    return db.session.scalar(db.select(db.func.count()).select_from(modelo))


def crear_pedido_en_bd(restaurante_id, plato, cliente=SUB_ANA, estado="pendiente"):
    """Un pedido escrito directamente en la base, para las pruebas que no lo crean por la API."""
    pedido = Pedido(cliente=cliente, restaurante_id=restaurante_id, estado=estado,
                    total=plato.precio)
    pedido.items.append(ItemPedido(plato_id=plato.id, cantidad=1, precio_unitario=plato.precio))
    db.session.add(pedido)
    db.session.commit()
    return pedido.id


def lineas(*pares):
    """El cuerpo de "crear pedido": {"lineas": [{"plato_id": ..., "cantidad": ...}, ...]}."""
    return {"lineas": [{"plato_id": plato_id, "cantidad": cantidad} for plato_id, cantidad in pares]}


# ------------------------------------------------------------ las seis obligatorias

def test_1_sin_sesion_crear_pedido_no_crea_nada(client, platos):
    """R6.1 · R2.5: sin token, crear un pedido responde 401 y no escribe nada."""
    silpancho = platos["Silpancho"]
    res = client.post(f"/api/restaurantes/{silpancho.restaurante_id}/pedidos",
                      json=lineas((silpancho.id, 2)))

    assert res.status_code == 401
    assert res.get_json()["code"] == "authorization_header_missing"
    assert contar(Pedido) == 0
    assert contar(ItemPedido) == 0


def test_2_cliente_no_puede_avanzar_el_estado(client, auth, platos):
    """R6.2 · R2.4: un cliente que pide el cambio de la cocina recibe 403."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)

    res = client.patch(f"/api/cocina/pedidos/{pedido_id}", json={"estado": "en_preparacion"},
                       headers=auth(CLIENTE))

    assert res.status_code == 403
    assert db.session.get(Pedido, pedido_id).estado == "pendiente"


def test_3_el_total_lo_calcula_el_servidor(client, auth, platos):
    """R6.3 · R1.3 · R1.4: un precio, total o cliente inventado en el JSON se ignora."""
    silpancho, sajta = platos["Silpancho"], platos["Sajta"]
    cuerpo = lineas((silpancho.id, 2), (sajta.id, 1))
    cuerpo["lineas"][0]["precio_unitario"] = "0.01"     # inventado: no debe usarse
    cuerpo["total"] = "1.00"                            # inventado: no debe usarse
    cuerpo["cliente"] = SUB_BETO                        # inventado: el cliente sale del token

    res = client.post(f"/api/restaurantes/{silpancho.restaurante_id}/pedidos", json=cuerpo,
                      headers=auth(CLIENTE))

    assert res.status_code == 201
    assert res.get_json()["total"] == "81.00"
    pedido = db.session.scalars(db.select(Pedido)).one()
    assert pedido.total == Decimal("81.00")                         # 2 × 25.50 + 1 × 30.00
    assert pedido.cliente == SUB_ANA
    precios = {item.plato_id: item.precio_unitario for item in pedido.items}
    assert precios == {silpancho.id: Decimal("25.50"), sajta.id: Decimal("30.00")}


def test_4_plato_no_disponible_rechaza_todo_el_pedido(client, auth, platos):
    """R6.4 · R1.5: un plato no disponible anula el pedido completo; no queda ninguna fila."""
    silpancho, lechon = platos["Silpancho"], platos["Lechón"]

    res = client.post(f"/api/restaurantes/{silpancho.restaurante_id}/pedidos",
                      json=lineas((silpancho.id, 1),     # este sí es válido...
                                  (lechon.id, 1)),       # ...pero este no está disponible
                      headers=auth(CLIENTE))

    assert res.status_code == 400
    assert contar(Pedido) == 0
    assert contar(ItemPedido) == 0


def test_5_pedido_de_otro_cliente_es_404(client, auth, platos):
    """R6.5 · R2.6: el pedido de otro cliente responde 404, no 403."""
    silpancho = platos["Silpancho"]
    pedido_de_beto = crear_pedido_en_bd(silpancho.restaurante_id, silpancho, cliente=SUB_BETO)
    headers = auth(CLIENTE, sub=SUB_ANA)

    assert client.get(f"/api/pedidos/{pedido_de_beto}", headers=headers).status_code == 404
    assert client.patch(f"/api/pedidos/{pedido_de_beto}", json={"estado": "cancelado"},
                        headers=headers).status_code == 404
    assert db.session.get(Pedido, pedido_de_beto).estado == "pendiente"


def test_6_cocina_no_puede_volver_de_listo_a_pendiente(client, auth, platos):
    """R6.6 · tabla de estados: solo se avanza un paso; listo -> pendiente se rechaza."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho, estado="listo")

    res = client.patch(f"/api/cocina/pedidos/{pedido_id}", json={"estado": "pendiente"},
                       headers=auth(COCINA))

    assert res.status_code == 400
    assert db.session.get(Pedido, pedido_id).estado == "listo"


# ------------------------------------------------------------ más reglas de R1 y R2

def test_plato_de_otro_restaurante_rechaza_el_pedido(client, auth, platos):
    """R1.5: todos los platos tienen que ser del restaurante del pedido."""
    silpancho, pique = platos["Silpancho"], platos["Pique macho"]

    res = client.post(f"/api/restaurantes/{silpancho.restaurante_id}/pedidos",
                      json=lineas((silpancho.id, 1), (pique.id, 1)), headers=auth(CLIENTE))

    assert res.status_code == 400
    assert contar(Pedido) == 0


@pytest.mark.parametrize("cantidad", ["0", "-1", "21", "dos", "1.5"])
def test_cantidad_fuera_de_rango_se_rechaza(client, auth, platos, cantidad):
    """R1.5: la cantidad es un entero entre 1 y 20."""
    silpancho = platos["Silpancho"]

    res = client.post(f"/api/restaurantes/{silpancho.restaurante_id}/pedidos",
                      json=lineas((silpancho.id, cantidad)), headers=auth(CLIENTE))

    assert res.status_code == 400
    assert contar(Pedido) == 0


def test_cliente_cancela_solo_si_esta_pendiente(client, auth, platos):
    """Tabla de estados: pendiente -> cancelado sí; en_preparacion -> cancelado no."""
    silpancho = platos["Silpancho"]
    pendiente = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)
    en_cocina = crear_pedido_en_bd(silpancho.restaurante_id, silpancho, estado="en_preparacion")
    headers = auth(CLIENTE)

    res = client.patch(f"/api/pedidos/{pendiente}", json={"estado": "cancelado"}, headers=headers)
    assert res.status_code == 200
    assert db.session.get(Pedido, pendiente).estado == "cancelado"

    res = client.patch(f"/api/pedidos/{en_cocina}", json={"estado": "cancelado"}, headers=headers)
    assert res.status_code == 400
    assert db.session.get(Pedido, en_cocina).estado == "en_preparacion"


def test_cocina_avanza_un_paso(client, auth, platos):
    """Tabla de estados: pendiente -> en_preparacion."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)

    res = client.patch(f"/api/cocina/pedidos/{pedido_id}", json={"estado": "en_preparacion"},
                       headers=auth(COCINA))

    assert res.status_code == 200
    assert res.get_json()["estado"] == "en_preparacion"
    assert db.session.get(Pedido, pedido_id).estado == "en_preparacion"


def test_la_carta_es_publica(client, platos):
    """R2.3: el listado y el detalle no piden login."""
    assert client.get("/api/restaurantes").status_code == 200
    assert client.get(f"/api/restaurantes/{platos['Silpancho'].restaurante_id}").status_code == 200


# Cada ruta protegida: sin token 401; con un rol que no tiene el permiso, 403.
# Si alguien borra el decorador de una de estas rutas, su caso falla.
RUTAS_PROTEGIDAS = [
    ("post", "/api/restaurantes/1/pedidos", COCINA),         # create:pedidos
    ("get", "/api/pedidos", COCINA),                         # read:mis-pedidos
    ("get", "/api/pedidos/1", COCINA),                       # read:mis-pedidos
    ("patch", "/api/pedidos/1", COCINA),                     # read:mis-pedidos
    ("get", "/api/cocina/pedidos", CLIENTE),                 # read:pedidos
    ("patch", "/api/cocina/pedidos/1", CLIENTE),             # update:pedidos
    ("post", "/api/restaurantes", CLIENTE),                  # write:carta
    ("put", "/api/restaurantes/1", CLIENTE),                 # write:carta
    ("post", "/api/restaurantes/1/platos", CLIENTE),         # write:carta
    ("delete", "/api/restaurantes/1", COCINA),               # delete:carta
]


@pytest.mark.parametrize("metodo, url, permisos_sin_acceso", RUTAS_PROTEGIDAS)
def test_rutas_protegidas(client, auth, metodo, url, permisos_sin_acceso):
    """R2.4 · R2.5: 401 sin token, 403 con token pero sin el permiso."""
    assert getattr(client, metodo)(url, json={}).status_code == 401
    assert getattr(client, metodo)(url, json={}, headers=auth(permisos_sin_acceso)).status_code == 403


def test_admin_ve_la_cola_pero_no_avanza(client, auth, platos):
    """R2.2: admin tiene read:pedidos pero no update:pedidos."""
    silpancho = platos["Silpancho"]
    pedido_id = crear_pedido_en_bd(silpancho.restaurante_id, silpancho)
    headers = auth(ADMIN)

    assert client.get("/api/cocina/pedidos", headers=headers).status_code == 200
    res = client.patch(f"/api/cocina/pedidos/{pedido_id}", json={"estado": "en_preparacion"},
                       headers=headers)
    assert res.status_code == 403
    assert db.session.get(Pedido, pedido_id).estado == "pendiente"
