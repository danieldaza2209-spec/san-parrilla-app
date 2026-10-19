import { e as defineMiddleware, s as sequence } from './chunks/render-context_Dt_WFfbm.mjs';
import { g as getAccessRule, S as SESSION_COOKIE, v as verifySessionToken, h as homeForRole } from './chunks/auth_CUmhD9Do.mjs';
import 'es-module-lexer';
import './chunks/astro-designed-error-pages_QRmgxunW.mjs';
import 'piccolore';
import './chunks/astro/server_DwdL0MGX.mjs';
import 'clsx';

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

const onRequest$1 = defineMiddleware(async (context, next) => {
  const { pathname } = context.url;
  if (!pathname.startsWith('/api/')) return next();

  const rule = getAccessRule(pathname, context.request.method);

  // Rutas públicas ("/api/auth/*"): no se toca nada.
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

const onRequest = sequence(
	
	onRequest$1
	
);

export { onRequest };
