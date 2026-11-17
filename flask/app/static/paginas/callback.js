// Auth0 vuelve aquí después del login: el SDK cambia el código por los tokens
// y la página vuelve a donde estaba el usuario.

import { pintarMensajeError } from "../blocks/mensaje-error/mensaje-error.js";
import { iniciarAuth, terminarLogin } from "../lib/auth.js";
import { $ } from "../lib/dom.js";

try {
  await iniciarAuth();
  await terminarLogin();
} catch (error) {
  console.error(error);
  pintarMensajeError($("[data-contenido]"), {
    codigo: "Auth0",
    titulo: "No se pudo ingresar",
    texto: error.error_description || error.message || "El login no terminó bien.",
    accion: { texto: "Volver al listado", href: "/restaurantes" },
  });
}
