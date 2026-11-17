import { avisar } from "../blocks/avisos/avisos.js";
import { $, campo, clonar, rellenar, segmentoDeLaUrl } from "../lib/dom.js";
import { api } from "../lib/api.js";
import { dinero, fechaHora } from "../lib/formato.js";
import { actualizarMigas, avisarError, iniciarPagina, mientrasEnvia, mostrarError } from "../lib/marco.js";

const pedidoId = segmentoDeLaUrl(1);   // /pedidos/<id>

await iniciarPagina({
  seccion: "pedidos",
  migas: [{ texto: "Mis pedidos", href: "/pedidos" }, { texto: `#${pedidoId}` }],
});

function pintar(pedido) {
  document.title = `Pedido #${pedido.id} · La Carta`;
  actualizarMigas([{ texto: "Mis pedidos", href: "/pedidos" }, { texto: `#${pedido.id}` }]);

  rellenar(document, {
    titulo: `Pedido #${pedido.id}`,
    restaurante: pedido.restaurante_nombre,
    estado: pedido.estado_etiqueta,
    fecha: fechaHora(pedido.fecha),
    "cantidad-items": pedido.items.length,
  });
  $('[data-enlace="restaurante"]').href = `/restaurantes/${pedido.restaurante_id}`;
  $('[data-accion="cancelar"]').hidden = pedido.estado !== "pendiente";

  const items = pedido.items.map((item) => {
    const fila = clonar("item");
    rellenar(fila, {
      descripcion: `${item.cantidad} × ${item.plato_nombre}`,
      "precio-unitario": `${dinero(item.precio_unitario)} c/u`,
      subtotal: dinero(Number(item.precio_unitario) * item.cantidad),
    });
    return fila;
  });
  const total = clonar("total");
  campo(total, "total").textContent = dinero(pedido.total);
  $('[data-lista="items"]').replaceChildren(...items, total);
}

document.addEventListener("click", async (evento) => {
  const boton = evento.target.closest('[data-accion="cancelar"]');
  if (!boton) return;
  try {
    const pedido = await mientrasEnvia(boton, () =>
      api(`/pedidos/${pedidoId}`, { metodo: "PATCH", cuerpo: { estado: "cancelado" } }));
    pintar(pedido);
    avisar(`Pedido #${pedido.id} cancelado.`);
  } catch (error) {
    avisarError(error);
  }
});

try {
  pintar(await api(`/pedidos/${pedidoId}`));
} catch (error) {
  mostrarError(error);
}
