// Login con el SDK de Auth0 para SPA (auth0-spa-js, cargado desde el CDN como window.auth0).
//
// El navegador hace el login (Authorization Code + PKCE) y guarda el access token;
// cada fetch a la API lo manda en Authorization: Bearer. Flask solo lo verifica.
//
// Como cada pantalla es una página aparte, el token se guarda en localStorage y
// se renueva con refresh tokens; así no se pierde la sesión al cambiar de página.

let cliente = null;

export async function iniciarAuth() {
  if (cliente) return cliente;

  const respuesta = await fetch("/api/config");
  if (!respuesta.ok) throw new Error("No se pudo leer /api/config");
  const config = await respuesta.json();

  cliente = await window.auth0.createAuth0Client({
    domain: config.domain,
    clientId: config.client_id,
    authorizationParams: {
      audience: config.audience,                       // el token es para nuestra API
      redirect_uri: `${window.location.origin}/callback`,
    },
    cacheLocation: "localstorage",
    useRefreshTokens: true,
  });
  return cliente;
}

// El access token, o null si no hay sesión (o ya no se puede renovar).
export async function obtenerToken() {
  if (!cliente || !(await cliente.isAuthenticated())) return null;
  try {
    return await cliente.getTokenSilently();
  } catch {
    return null;
  }
}

// { token, usuario, permisos } o null.
// Los permisos se leen del token solo para mostrar u ocultar botones:
// quien los hace cumplir es @requires_auth en Flask.
export async function obtenerSesion() {
  const token = await obtenerToken();
  if (!token) return null;
  const usuario = (await cliente.getUser()) ?? {};
  return { token, usuario, permisos: leerPermisos(token) };
}

export function ingresar() {
  const volverA = window.location.pathname + window.location.search;
  return cliente.loginWithRedirect({ appState: { volverA } });
}

export function salir() {
  // Cierra también la sesión que Auth0 guarda en su página; si no, "Ingresar"
  // volvería a entrar con la misma cuenta sin preguntar.
  return cliente.logout({ logoutParams: { returnTo: `${window.location.origin}/restaurantes` } });
}

// En /callback: Auth0 vuelve con ?code=...&state=...; el SDK lo cambia por los tokens.
export async function terminarLogin() {
  const { appState } = await cliente.handleRedirectCallback();
  window.location.replace(rutaSegura(appState?.volverA));
}

function leerPermisos(token) {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const bytes = Uint8Array.from(atob(base64), (letra) => letra.charCodeAt(0));
    const payload = JSON.parse(new TextDecoder().decode(bytes));
    return Array.isArray(payload.permissions) ? payload.permissions : [];
  } catch {
    return [];
  }
}

// Solo rutas de este sitio: nada de redirigir a otro dominio.
function rutaSegura(ruta) {
  if (typeof ruta === "string" && ruta.startsWith("/") && !ruta.startsWith("//") && !ruta.includes("\\")) {
    return ruta;
  }
  return "/restaurantes";
}
