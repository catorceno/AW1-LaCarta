// migas: "Restaurantes" siempre primero; después los pasos de la página.
// Un paso con href es un enlace; el último, sin href, es la página actual.

export function pintarMigas(migas, pasos = []) {
  migas.replaceChildren(crearPaso({ texto: "Restaurantes", href: "/restaurantes" }));
  for (const paso of pasos) {
    const sep = document.createElement("span");
    sep.className = "migas__sep";
    sep.textContent = "/";
    migas.append(sep, crearPaso(paso));
  }
}

function crearPaso({ texto, href }) {
  const nodo = document.createElement(href ? "a" : "span");
  nodo.className = href ? "migas__enlace" : "migas__actual";
  if (href) nodo.href = href;
  nodo.textContent = texto;
  return nodo;
}
