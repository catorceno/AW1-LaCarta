// /empleados/crear y /empleados/<id>/editar usan esta misma página.

import { avisarAlCargar } from "../blocks/avisos/avisos.js";
import { ErrorApi, api } from "../lib/api.js";
import { $, leerFormulario, rellenar, segmentoDeLaUrl } from "../lib/dom.js";
import { actualizarMigas, avisarError, iniciarPagina, mientrasEnvia, mostrarError } from "../lib/marco.js";

const editando = window.location.pathname.endsWith("/editar");
const empleadoId = editando ? segmentoDeLaUrl(1) : null;
const formulario = $('[data-formulario="empleado"]');

const { sesion, puede } = await iniciarPagina({
  seccion: "empleados",
  migas: [{ texto: "Empleados", href: "/empleados" }, { texto: editando ? "Editar" : "Nuevo" }],
});

try {
  // La API exige write:empleados al guardar; aquí solo se evita mostrar un formulario inútil
  if (!sesion) throw new ErrorApi(401);
  if (!puede("write:empleados")) throw new ErrorApi(403);

  const restaurantes = await api("/restaurantes");
  const selector = $("[data-restaurantes]");
  for (const r of restaurantes) {
    selector.add(new Option(`${r.nombre} (${r.ciudad})`, r.id));
  }

  if (editando) {
    const empleado = await api(`/empleados/${empleadoId}`);
    const nombre = `${empleado.nombre} ${empleado.apellido}`;
    document.title = "Editar empleado · La Carta";
    actualizarMigas([{ texto: "Empleados", href: "/empleados" }, { texto: "Editar" }]);
    rellenar(document, {
      titulo: `Editar ${nombre}`,
      boton: "Guardar cambios",
      "nota-fecha": "vacía: se mantiene la actual",
    });
    $('[data-enlace="cancelar"]').href = `/empleados/${empleadoId}`;
    for (const campo of ["nombre", "apellido", "ci", "restaurante_id", "salario", "fecha_ingreso",
      "correo", "telefono", "direccion"]) {
      formulario.elements[campo].value = empleado[campo] ?? "";
    }
    formulario.elements.activo.checked = empleado.activo;
  }
} catch (error) {
  mostrarError(error);
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const cuerpo = leerFormulario(formulario);
  try {
    const empleado = await mientrasEnvia(formulario.querySelector('[type="submit"]'), () => (editando
      ? api(`/empleados/${empleadoId}`, { metodo: "PUT", cuerpo })
      : api("/empleados", { metodo: "POST", cuerpo })));
    avisarAlCargar(editando
      ? "Empleado actualizado."
      : `Empleado ${empleado.nombre} ${empleado.apellido} creado.`);
    window.location.assign(`/empleados/${empleado.id}`);
  } catch (error) {
    // Error de validación (400): el formulario queda con lo que el usuario escribió
    avisarError(error);
  }
});
