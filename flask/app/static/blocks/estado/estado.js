// estado: el modificador refleja el dato (sí/no); el CSS decide el color.

export function pintarEstado(nodo, si, textoSi, textoNo) {
  nodo.classList.toggle("estado--si", si);
  nodo.classList.toggle("estado--no", !si);
  nodo.textContent = si ? textoSi : textoNo;
}
