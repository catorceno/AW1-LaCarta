// mensaje-error: reemplaza el contenido de la página por el mensaje.
// accion: { texto, href } para un enlace, o { texto, alHacerClic } para un botón.

export function pintarMensajeError(contenedor, { codigo, titulo, texto, accion }) {
  const bloque = document.createElement("div");
  bloque.className = "mensaje-error";

  const nodoCodigo = document.createElement("p");
  nodoCodigo.className = "mensaje-error__codigo";
  nodoCodigo.textContent = codigo;

  const nodoTitulo = document.createElement("h1");
  nodoTitulo.className = "mensaje-error__titulo";
  nodoTitulo.textContent = titulo;

  const nodoTexto = document.createElement("p");
  nodoTexto.className = "mensaje-error__texto";
  nodoTexto.textContent = texto;

  bloque.append(nodoCodigo, nodoTitulo, nodoTexto);

  if (accion) {
    const boton = document.createElement(accion.href ? "a" : "button");
    boton.className = "mensaje-error__accion boton";
    boton.textContent = accion.texto;
    if (accion.href) {
      boton.href = accion.href;
    } else {
      boton.type = "button";
      boton.classList.add("boton--primario");
      boton.addEventListener("click", () => accion.alHacerClic());
    }
    bloque.append(boton);
  }

  contenedor.replaceChildren(bloque);
}
