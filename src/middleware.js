import { defineMiddleware } from 'astro:middleware';
import { SESSION_COOKIE, getAccessRule, homeForRole, verifySessionToken } from './lib/auth.js';

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

function hardenHeaders(response) {
  try {
    response.headers.set('Cache-Control', 'no-store');
    response.headers.set('X-Robots-Tag', 'noindex, nofollow');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('Referrer-Policy', 'same-origin');
  } catch {
    // Algunas respuestas (redirects) tienen headers inmutables; no es crítico.
  }
  return response;
}

export const onRequest = defineMiddleware(async (context, next) => {
  const { pathname } = context.url;
  const rule = getAccessRule(pathname, context.request.method);

  // Rutas públicas (carta "/", "/login", "/api/auth/*"): no se toca nada.
  if (!rule) return next();

  const token = context.cookies.get(SESSION_COOKIE)?.value;
  const session = token ? verifySessionToken(token) : null;
  const isApi = rule.kind === 'api';

  // 1) Sin sesión válida
  if (!session) {
    if (isApi) return json(401, { error: 'Sesión requerida. Inicia sesión de nuevo.' });
    const loginUrl = `/login?next=${encodeURIComponent(pathname + context.url.search)}`;
    return hardenHeaders(context.redirect(loginUrl, 302));
  }

  // 2) Sesión válida pero rol sin permiso
  if (!rule.roles.includes(session.role)) {
    if (isApi) return json(403, { error: 'No tienes permiso para esta acción.' });
    return hardenHeaders(context.redirect(homeForRole(session.role), 302));
  }

  // 3) Autorizado: el usuario queda disponible para layouts y endpoints
  context.locals.user = session;
  return hardenHeaders(await next());
});
