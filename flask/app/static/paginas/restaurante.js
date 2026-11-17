import { avisar, avisarAlCargar } from "../blocks/avisos/avisos.js";
import { pintarEstado } from "../blocks/estado/estado.js";
import { pintarLista } from "../blocks/lista/lista.js";
import { pintarValor } from "../blocks/propiedades/propiedades.js";
import { api } from "../lib/api.js";
import { $, $$, campo, clonar, leerFormulario, rellenar, segmentoDeLaUrl } from "../lib/dom.js";
import { dinero } from "../lib/formato.js";
import { actualizarMigas, avisarError, iniciarPagina, mientrasEnvia, mostrarError } from "../lib/marco.js";

const restauranteId = segmentoDeLaUrl(1);   // /restaurantes/<id>

await iniciarPagina({ seccion: "restaurantes" });
$('[data-enlace="editar"]').href = `/restaurantes/${restauranteId}/editar`;

async function cargar() {
  const { restaurante, platos } = await api(`/restaurantes/${restauranteId}`);

  document.title = `${restaurante.nombre} · La Carta`;
  actualizarMigas([{ texto: restaurante.nombre }]);

  rellenar(document, {
    nombre: restaurante.nombre,
    ciudad: restaurante.ciudad,
    "cantidad-platos": platos.length,
  });
  pintarValor(campo(document, "direccion"), restaurante.direccion, "No registrada");
  pintarValor(campo(document, "telefono"), restaurante.telefono, "No registrado");

  pintarLista($('[data-lista="platos"]'), platos, (plato) => {
    const item = clonar("plato");
    rellenar(item, { nombre: plato.nombre, precio: dinero(plato.precio) });
    pintarEstado($("[data-estado]", item), plato.disponible, "Disponible", "No disponible");
    return item;
  }, `Todavía no hay platos en ${restaurante.nombre}.`);

  const disponibles = platos.filter((plato) => plato.disponible);
  pintarLista($('[data-lista="pedido"]'), disponibles, (plato) => {
    const item = clonar("linea-pedido");
    const id = `cantidad-${plato.id}`;
    rellenar(item, { nombre: plato.nombre, precio: dinero(plato.precio) });
    campo(item, "nombre").htmlFor = id;
    const cantidad = $("[data-cantidad]", item);
    cantidad.id = id;
    cantidad.dataset.plato = plato.id;
    cantidad.setAttribute("aria-label", `Cantidad de ${plato.nombre}`);
    return item;
  }, "No hay platos disponibles en este momento.");
  $("[data-enviar-pedido]").hidden = disponibles.length === 0;
}

// ---------------------------------------------------------------- acciones

document.addEventListener("click", async (evento) => {
  const boton = evento.target.closest('[data-accion="eliminar"]');
  if (!boton) return;
  try {
    await mientrasEnvia(boton, () => api(`/restaurantes/${restauranteId}`, { metodo: "DELETE" }));
    avisarAlCargar("Restaurante eliminado.");
    window.location.assign("/restaurantes");
  } catch (error) {
    avisarError(error);
  }
});

$('[data-formulario="plato"]').addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const formulario = evento.currentTarget;
  try {
    await mientrasEnvia(formulario.querySelector('[type="submit"]'), () =>
      api(`/restaurantes/${restauranteId}/platos`, { metodo: "POST", cuerpo: leerFormulario(formulario) }));
    formulario.reset();
    await cargar();
    avisar("Plato creado.");
  } catch (error) {
    avisarError(error);
  }
});

$('[data-formulario="pedido"]').addEventListener("submit", async (evento) => {
  evento.preventDefault();
  // Solo plato y cantidad (R1.4): el precio y el total los pone el servidor
  const lineas = $$("[data-cantidad]", evento.currentTarget)
    .filter((entrada) => !["", "0"].includes(entrada.value.trim()))
    .map((entrada) => ({ plato_id: Number(entrada.dataset.plato), cantidad: entrada.value.trim() }));
  try {
    const pedido = await mientrasEnvia(evento.currentTarget.querySelector('[type="submit"]'), () =>
      api(`/restaurantes/${restauranteId}/pedidos`, { metodo: "POST", cuerpo: { lineas } }));
    avisarAlCargar(`Pedido #${pedido.id} creado.`);
    window.location.assign(`/pedidos/${pedido.id}`);
  } catch (error) {
    avisarError(error);
  }
});

try {
  await cargar();
} catch (error) {
  mostrarError(error);
}
