// usuario: "Ingresar" sin sesión; nombre + "Cerrar sesión" con sesión.
// El botón es otro bloque (boton) dentro de este.

export function pintarUsuario(contenedor, sesion, { ingresar, salir }) {
  contenedor.replaceChildren();

  if (!sesion) {
    contenedor.append(crearBoton("Ingresar", ["boton"], ingresar));
    return;
  }

  const nombre = document.createElement("span");
  nombre.className = "usuario__nombre";
  nombre.textContent = sesion.usuario.name || sesion.usuario.email || "";
  contenedor.append(nombre, crearBoton("Cerrar sesión", ["boton", "boton--fantasma"], salir));
}

function crearBoton(texto, clases, alHacerClic) {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.classList.add(...clases);
  boton.textContent = texto;
  boton.addEventListener("click", () => alHacerClic());
  return boton;
}
