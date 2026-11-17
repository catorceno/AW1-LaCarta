// Cómo se muestran los datos que llegan de la API (montos como texto "25.50", fechas ISO).

export function dinero(monto) {
  return `${Number(monto).toFixed(2)} Bs.`;
}

// "2026-11-16T14:05:00+00:00" -> "16/11/2026 14:05 (UTC)"
export function fechaHora(iso) {
  const f = new Date(iso);
  const dos = (n) => String(n).padStart(2, "0");
  return `${dos(f.getUTCDate())}/${dos(f.getUTCMonth() + 1)}/${f.getUTCFullYear()} ${dos(f.getUTCHours())}:${dos(f.getUTCMinutes())} (UTC)`;
}

// "2026-11-16" -> "16/11/2026"
export function fecha(iso) {
  const [anio, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${anio}`;
}

export function plural(cantidad, singular, pluralTexto) {
  return `${cantidad} ${cantidad === 1 ? singular : pluralTexto}`;
}
