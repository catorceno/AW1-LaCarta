// fetch a /api/ con el token de Auth0. Devuelve el JSON o lanza ErrorApi.

import { obtenerToken } from "./auth.js";

export class ErrorApi extends Error {
  constructor(status, cuerpo) {
    super(cuerpo?.description || `Error ${status}`);
    this.status = status;
    this.code = cuerpo?.code;
  }
}

export async function api(ruta, { metodo = "GET", cuerpo } = {}) {
  const headers = { Accept: "application/json" };

  const token = await obtenerToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  if (cuerpo !== undefined) headers["Content-Type"] = "application/json";

  const respuesta = await fetch(`/api${ruta}`, {
    method: metodo,
    headers,
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });

  if (respuesta.status === 204) return null;

  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, datos);
  return datos;
}
