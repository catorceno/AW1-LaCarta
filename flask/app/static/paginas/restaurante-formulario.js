// /restaurantes/crear y /restaurantes/<id>/editar usan esta misma página.

import { avisarAlCargar } from "../blocks/avisos/avisos.js";
import { ErrorApi, api } from "../lib/api.js";
import { $, leerFormulario, rellenar, segmentoDeLaUrl } from "../lib/dom.js";
import { actualizarMigas, avisarError, iniciarPagina, mientrasEnvia, mostrarError } from "../lib/marco.js";

const editando = window.location.pathname.endsWith("/editar");
const restauranteId = editando ? segmentoDeLaUrl(1) : null;
const formulario = $('[data-formulario="restaurante"]');

const { sesion, puede } = await iniciarPagina({
  seccion: editando ? "restaurantes" : "nuevo-restaurante",
  migas: editando ? [] : [{ texto: "Nuevo" }],
});

try {
  // La API exige write:carta al guardar; aquí solo se evita mostrar un formulario inútil
  if (!sesion) throw new ErrorApi(401);
  if (!puede("write:carta")) throw new ErrorApi(403);

  if (editando) {
    const { restaurante } = await api(`/restaurantes/${restauranteId}`);
    document.title = "Editar restaurante · La Carta";
    actualizarMigas([{ texto: restaurante.nombre, href: `/restaurantes/${restauranteId}` }, { texto: "Editar" }]);
    rellenar(document, { titulo: `Editar ${restaurante.nombre}`, boton: "Guardar cambios" });
    $('[data-enlace="cancelar"]').href = `/restaurantes/${restauranteId}`;
    for (const nombre of ["nombre", "ciudad", "direccion", "telefono"]) {
      formulario.elements[nombre].value = restaurante[nombre] ?? "";
    }
  }
} catch (error) {
  mostrarError(error);
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const cuerpo = leerFormulario(formulario);
  try {
    await mientrasEnvia(formulario.querySelector('[type="submit"]'), () => (editando
      ? api(`/restaurantes/${restauranteId}`, { metodo: "PUT", cuerpo })
      : api("/restaurantes", { metodo: "POST", cuerpo })));
    avisarAlCargar(editando ? "Restaurante actualizado." : "Restaurante creado.");
    window.location.assign(editando ? `/restaurantes/${restauranteId}` : "/restaurantes");
  } catch (error) {
    avisarError(error);
  }
});
