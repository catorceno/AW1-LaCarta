// nav: arma los enlaces según los permisos del token y marca la sección actual.

const ITEMS = [
  { seccion: "restaurantes", texto: "Restaurantes", icono: "☰", href: "/restaurantes" },
  { seccion: "empleados", texto: "Empleados", icono: "👥", href: "/empleados" },
  { seccion: "nuevo-restaurante", texto: "Nuevo restaurante", icono: "＋", href: "/restaurantes/crear", permiso: "write:carta" },
  { seccion: "pedidos", texto: "Mis pedidos", icono: "🧾", href: "/pedidos", permiso: "read:mis-pedidos" },
  { seccion: "cocina", texto: "Cocina", icono: "🍳", href: "/cocina", permiso: "read:pedidos" },
];

export function pintarNav(nav, permisos, seccionActual) {
  nav.replaceChildren();
  for (const item of ITEMS) {
    if (item.permiso && !permisos.includes(item.permiso)) continue;

    const enlace = document.createElement("a");
    enlace.className = "nav__item";
    enlace.classList.toggle("nav__item--activo", item.seccion === seccionActual);
    enlace.href = item.href;

    const icono = document.createElement("span");
    icono.className = "nav__icono";
    icono.setAttribute("aria-hidden", "true");
    icono.textContent = item.icono;

    const texto = document.createElement("span");
    texto.textContent = item.texto;

    enlace.append(icono, texto);
    nav.append(enlace);
  }
}
