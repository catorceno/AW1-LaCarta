import { pintarLista } from "../blocks/lista/lista.js";
import { api } from "../lib/api.js";
import { $, campo, clonar, rellenar } from "../lib/dom.js";
import { dinero, plural } from "../lib/formato.js";
import { iniciarPagina, mostrarError } from "../lib/marco.js";

await iniciarPagina({ seccion: "pedidos", migas: [{ texto: "Mis pedidos" }] });

try {
  const pedidos = await api("/pedidos");     // solo los del usuario del token

  campo(document, "resumen").textContent = plural(pedidos.length, "pedido", "pedidos");

  pintarLista($('[data-lista="pedidos"]'), pedidos, (pedido) => {
    const item = clonar("pedido");
    $("[data-enlace]", item).href = `/pedidos/${pedido.id}`;
    rellenar(item, {
      titulo: `Pedido #${pedido.id} · ${pedido.restaurante_nombre}`,
      estado: pedido.estado_etiqueta,
      total: dinero(pedido.total),
    });
    return item;
  }, "Todavía no hiciste ningún pedido.");
} catch (error) {
  mostrarError(error);
}
