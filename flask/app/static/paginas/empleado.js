import { avisarAlCargar } from "../blocks/avisos/avisos.js";
import { pintarEstado } from "../blocks/estado/estado.js";
import { pintarValor } from "../blocks/propiedades/propiedades.js";
import { api } from "../lib/api.js";
import { $, $$, campo, rellenar, segmentoDeLaUrl } from "../lib/dom.js";
import { dinero, fecha } from "../lib/formato.js";
import { actualizarMigas, avisarError, iniciarPagina, mientrasEnvia, mostrarError } from "../lib/marco.js";

const empleadoId = segmentoDeLaUrl(1);   // /empleados/<id>

await iniciarPagina({ seccion: "empleados", migas: [{ texto: "Empleados", href: "/empleados" }] });
$('[data-enlace="editar"]').href = `/empleados/${empleadoId}/editar`;

document.addEventListener("click", async (evento) => {
  const boton = evento.target.closest('[data-accion="eliminar"]');
  if (!boton) return;
  try {
    await mientrasEnvia(boton, () => api(`/empleados/${empleadoId}`, { metodo: "DELETE" }));
    avisarAlCargar("Empleado eliminado.");
    window.location.assign("/empleados");
  } catch (error) {
    avisarError(error);
  }
});

try {
  const empleado = await api(`/empleados/${empleadoId}`);
  const nombre = `${empleado.nombre} ${empleado.apellido}`;

  document.title = `${nombre} · La Carta`;
  actualizarMigas([{ texto: "Empleados", href: "/empleados" }, { texto: nombre }]);

  rellenar(document, { nombre, restaurante: empleado.restaurante_nombre });
  $('[data-enlace="restaurante"]').href = `/restaurantes/${empleado.restaurante_id}`;
  pintarEstado($("[data-estado]"), empleado.activo, "Activo", "Inactivo");

  // La API solo manda los datos privados a quien tiene write:empleados
  const conPrivados = "ci" in empleado;
  for (const fila of $$("[data-privado]")) fila.hidden = !conPrivados;
  if (conPrivados) {
    rellenar(document, {
      ci: empleado.ci,
      salario: dinero(empleado.salario),
      fecha_ingreso: fecha(empleado.fecha_ingreso),
    });
    pintarValor(campo(document, "correo"), empleado.correo, "No registrado");
    pintarValor(campo(document, "telefono"), empleado.telefono, "No registrado");
    pintarValor(campo(document, "direccion"), empleado.direccion, "No registrada");
  }
} catch (error) {
  mostrarError(error);
}
