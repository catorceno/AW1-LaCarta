// Ayudas para llenar el HTML. JavaScript encuentra los nodos por data-*, nunca por
// clases de estilo: un cambio de diseño no rompe la lógica.

export function $(selector, raiz = document) {
  return raiz.querySelector(selector);
}

export function $$(selector, raiz = document) {
  return [...raiz.querySelectorAll(selector)];
}

// Copia del primer nodo de <template data-plantilla="nombre">.
export function clonar(nombre) {
  return $(`template[data-plantilla="${nombre}"]`).content.firstElementChild.cloneNode(true);
}

// El nodo con data-campo="nombre" dentro de raiz.
export function campo(raiz, nombre) {
  return $(`[data-campo="${nombre}"]`, raiz);
}

// Escribe cada valor como texto en su data-campo (textContent: sin riesgo de inyectar HTML).
export function rellenar(raiz, valores) {
  for (const [nombre, valor] of Object.entries(valores)) {
    const nodo = campo(raiz, nombre);
    if (nodo) nodo.textContent = valor;
  }
}

// /restaurantes/3/editar -> segmentoDeLaUrl(1) === 3
export function segmentoDeLaUrl(posicion) {
  const partes = window.location.pathname.split("/").filter(Boolean);
  return Number(partes[posicion]);
}

// Los valores de un formulario como objeto; los checkbox como true/false.
export function leerFormulario(formulario) {
  const datos = {};
  for (const control of formulario.elements) {
    if (!control.name) continue;
    datos[control.name] = control.type === "checkbox" ? control.checked : control.value.trim();
  }
  return datos;
}
