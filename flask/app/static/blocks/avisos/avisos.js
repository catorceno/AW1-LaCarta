// avisos: muestra un mensaje de éxito o error (bloque aviso). Cada aviso nuevo
// reemplaza al anterior, como el mensaje flash que llegaba con cada respuesta.
// avisarAlCargar() guarda el mensaje para la próxima página: después de crear
// algo se navega a otra pantalla, y el aviso tiene que aparecer allí.

const CLAVE = "lacarta:aviso";

function contenedor() {
  return document.querySelector("[data-avisos]");
}

export function avisar(texto, tipo = "exito") {
  const avisos = contenedor();
  const aviso = document.createElement("div");
  aviso.className = `aviso aviso--${tipo}`;
  aviso.setAttribute("role", tipo === "error" ? "alert" : "status");
  aviso.textContent = texto;
  avisos.replaceChildren(aviso);
  avisos.classList.remove("avisos--vacio");
}

export function limpiarAvisos() {
  const avisos = contenedor();
  avisos.replaceChildren();
  avisos.classList.add("avisos--vacio");
}

export function avisarAlCargar(texto, tipo = "exito") {
  try {
    sessionStorage.setItem(CLAVE, JSON.stringify({ texto, tipo }));
  } catch {
    // sin sessionStorage el aviso simplemente no se muestra
  }
}

export function mostrarAvisoPendiente() {
  try {
    const guardado = sessionStorage.getItem(CLAVE);
    if (!guardado) return;
    sessionStorage.removeItem(CLAVE);
    const { texto, tipo } = JSON.parse(guardado);
    avisar(texto, tipo);
  } catch {
    // un valor corrupto no debe romper la página
  }
}
