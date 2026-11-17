import { pintarEstado } from "../blocks/estado/estado.js";
import { pintarLista } from "../blocks/lista/lista.js";
import { api } from "../lib/api.js";
import { $, campo, clonar, rellenar } from "../lib/dom.js";
import { plural } from "../lib/formato.js";
import { iniciarPagina, mostrarError } from "../lib/marco.js";

await iniciarPagina({ seccion: "empleados", migas: [{ texto: "Empleados" }] });

try {
  const empleados = await api("/empleados");

  campo(document, "resumen").textContent = plural(empleados.length, "empleado", "empleados");

  pintarLista($('[data-lista="empleados"]'), empleados, (empleado) => {
    const item = clonar("empleado");
    $("[data-enlace]", item).href = `/empleados/${empleado.id}`;
    rellenar(item, {
      nombre: `${empleado.apellido}, ${empleado.nombre}`,
      restaurante: empleado.restaurante_nombre,
    });
    pintarEstado($("[data-estado]", item), empleado.activo, "Activo", "Inactivo");
    return item;
  }, "Todavía no hay empleados.");
} catch (error) {
  mostrarError(error);
}
