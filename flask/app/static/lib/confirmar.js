// Confirmación antes de una acción: <button data-confirmar="¿Eliminar…?">.
//
// Un solo listener para toda la página, en fase de captura: corre antes que el
// listener de la acción y, si el usuario cancela, el clic no llega a ella.
// Reemplaza los onclick="return confirm(…)" escritos en el HTML.

export function activarConfirmaciones() {
  document.addEventListener(
    "click",
    (evento) => {
      const boton = evento.target.closest("[data-confirmar]");
      if (boton && !window.confirm(boton.dataset.confirmar)) {
        evento.preventDefault();
        evento.stopPropagation();
      }
    },
    true,
  );
}
