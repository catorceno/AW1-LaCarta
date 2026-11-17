// lista: vacía la <ul>, agrega un ítem por elemento o el mensaje de lista vacía.

export function pintarLista(ul, elementos, crearItem, textoVacio) {
  ul.replaceChildren(...elementos.map(crearItem));
  if (elementos.length === 0) {
    const vacio = document.createElement("li");
    vacio.className = "lista__item lista__item--vacio";
    vacio.textContent = textoVacio;
    ul.append(vacio);
  }
}
