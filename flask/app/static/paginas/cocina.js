import { avisar } from "../blocks/avisos/avisos.js";
import { pintarLista } from "../blocks/lista/lista.js";
import { api } from "../lib/api.js";
import { $, campo, clonar, rellenar } from "../lib/dom.js";
import { avisarError, iniciarPagina, mientrasEnvia, mostrarError } from "../lib/marco.js";

const { puede } = await iniciarPagina({ seccion: "cocina", migas: [{ texto: "Cocina" }] });

async function cargar() {
  const pedidos = await api("/cocina/pedidos");    // el más antiguo primero

  const cantidad = pedidos.length;
  campo(document, "resumen").textContent =
    `${cantidad} ${cantidad === 1 ? "pedido activo" : "pedidos activos"} · recarga la página para ver los nuevos`;

  pintarLista($('[data-lista="cocina"]'), pedidos, (pedido) => {
    const item = clonar("pedido-cocina");
    rellenar(item, {
      titulo: `#${pedido.id} · ${pedido.restaurante_nombre}`,
      items: pedido.items.map((i) => `${i.cantidad} × ${i.plato_nombre}`).join(", "),
      estado: pedido.estado_etiqueta,
    });
    const boton = $('[data-accion="avanzar"]', item);
    boton.hidden = !puede("update:pedidos");     // el admin ve la cola pero no la avanza
    boton.textContent = `Pasar a ${pedido.siguiente_etiqueta}`;
    boton.dataset.pedido = pedido.id;
    boton.dataset.estado = pedido.siguiente_estado;
    return item;
  }, "No hay pedidos activos.");
}

document.addEventListener("click", async (evento) => {
  const boton = evento.target.closest('[data-accion="avanzar"]');
  if (!boton) return;
  try {
    const pedido = await mientrasEnvia(boton, () =>
      api(`/cocina/pedidos/${boton.dataset.pedido}`, { metodo: "PATCH", cuerpo: { estado: boton.dataset.estado } }));
    await cargar();
    avisar(`Pedido #${pedido.id}: ${pedido.estado_etiqueta}.`);
  } catch (error) {
    avisarError(error);
  }
});

try {
  await cargar();
} catch (error) {
  mostrarError(error);
}
