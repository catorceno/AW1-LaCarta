import { pintarLista } from "../blocks/lista/lista.js";
import { api } from "../lib/api.js";
import { $, clonar, campo, rellenar } from "../lib/dom.js";
import { plural } from "../lib/formato.js";
import { iniciarPagina, mostrarError } from "../lib/marco.js";

const ciudad = new URLSearchParams(window.location.search).get("ciudad")?.trim() ?? "";

await iniciarPagina({ seccion: "restaurantes" });

$('input[name="ciudad"]').value = ciudad;
$("[data-quitar-filtro]").hidden = !ciudad;

try {
  const consulta = ciudad ? `?ciudad=${encodeURIComponent(ciudad)}` : "";
  const restaurantes = await api(`/restaurantes${consulta}`);
  const enCiudad = ciudad ? ` en "${ciudad}"` : "";

  campo(document, "resumen").textContent = plural(restaurantes.length, "restaurante", "restaurantes") + enCiudad;

  pintarLista($('[data-lista="restaurantes"]'), restaurantes, (r) => {
    const item = clonar("restaurante");
    $("[data-enlace]", item).href = `/restaurantes/${r.id}`;
    rellenar(item, {
      nombre: r.nombre,
      ciudad: r.ciudad,
      platos: plural(r.cantidad_platos, "plato", "platos"),
    });
    return item;
  }, `No hay restaurantes${enCiudad}.`);
} catch (error) {
  mostrarError(error);
}
