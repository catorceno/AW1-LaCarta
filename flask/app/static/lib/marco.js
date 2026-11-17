// Lo común a todas las páginas: sesión, barra lateral, usuario, migas, avisos
// y cómo se muestran los errores de la API.

import { pintarMigas } from "../blocks/migas/migas.js";
import { pintarNav } from "../blocks/nav/nav.js";
import { pintarUsuario } from "../blocks/usuario/usuario.js";
import { avisar, mostrarAvisoPendiente } from "../blocks/avisos/avisos.js";
import { pintarMensajeError } from "../blocks/mensaje-error/mensaje-error.js";
import { ErrorApi } from "./api.js";
import { iniciarAuth, ingresar, obtenerSesion, salir } from "./auth.js";
import { activarConfirmaciones } from "./confirmar.js";
import { $, $$ } from "./dom.js";

// Devuelve { sesion, puede(permiso) }.
export async function iniciarPagina({ seccion, migas = [] } = {}) {
  activarConfirmaciones();
  mostrarAvisoPendiente();
  pintarMigas($("[data-migas]"), migas);

  let sesion = null;
  try {
    await iniciarAuth();
    sesion = await obtenerSesion();
  } catch (error) {
    console.error(error);
    avisar("No se pudo conectar con Auth0. Puedes ver la carta, pero no ingresar.", "error");
  }

  const permisos = sesion?.permisos ?? [];
  const puede = (permiso) => permisos.includes(permiso);

  pintarNav($("[data-nav]"), permisos, seccion);
  pintarUsuario($("[data-usuario]"), sesion, { ingresar, salir });

  // <a data-requiere="write:carta" hidden>: se muestra solo con ese permiso.
  // Es comodidad: la API rechaza igual a quien no lo tiene.
  for (const nodo of $$("[data-requiere]")) {
    nodo.hidden = !puede(nodo.dataset.requiere);
  }

  return { sesion, puede };
}

export function actualizarMigas(migas) {
  pintarMigas($("[data-migas]"), migas);
}

// Cuando no se pudo cargar la página: el contenido se reemplaza por el mensaje.
export function mostrarError(error) {
  const contenido = $("[data-contenido]");

  if (!(error instanceof ErrorApi)) {
    console.error(error);
    pintarMensajeError(contenido, {
      codigo: "Error",
      titulo: "No se pudo cargar",
      texto: "No se pudo conectar con el servidor. Intenta de nuevo en un momento.",
      accion: { texto: "Volver al listado", href: "/restaurantes" },
    });
    return;
  }

  const mensajes = {
    401: {
      titulo: "Ingresa para continuar",
      texto: "Necesitas iniciar sesión para ver esta página.",
      accion: { texto: "Ingresar con Auth0", alHacerClic: ingresar },
    },
    403: {
      titulo: "Acceso denegado",
      texto: "Tu cuenta no tiene permiso para esto.",
      accion: { texto: "Volver", href: "/restaurantes" },
    },
    404: {
      titulo: "Recurso no encontrado",
      texto: "El restaurante o la página que buscas no existe.",
      accion: { texto: "Volver al listado", href: "/restaurantes" },
    },
  };
  const mensaje = mensajes[error.status] ?? {
    titulo: "No se pudo procesar",
    texto: error.message,
    accion: { texto: "Volver al listado", href: "/restaurantes" },
  };
  pintarMensajeError(contenido, { codigo: error.status, ...mensaje });
}

// Cuando falló una acción (guardar, eliminar…): la página queda, con un aviso.
export function avisarError(error) {
  if (!(error instanceof ErrorApi)) console.error(error);
  const textos = {
    401: "Tu sesión terminó. Vuelve a ingresar.",
    403: "Tu cuenta no tiene permiso para esto.",
  };
  const texto = error instanceof ErrorApi
    ? textos[error.status] ?? error.message
    : "No se pudo conectar con el servidor.";
  avisar(texto, "error");
}

// Mientras se envía, el botón se desactiva para que no se mande dos veces.
export async function mientrasEnvia(boton, tarea) {
  boton.disabled = true;
  try {
    return await tarea();
  } finally {
    boton.disabled = false;
  }
}
