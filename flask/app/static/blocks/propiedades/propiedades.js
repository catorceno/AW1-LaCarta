// propiedades: escribe un valor; si no hay, el texto de reemplazo y el modificador --vacio.

export function pintarValor(dd, valor, textoVacio) {
  const vacio = valor === null || valor === undefined || valor === "";
  dd.classList.toggle("propiedades__valor--vacio", vacio);
  dd.textContent = vacio ? textoVacio : valor;
}
