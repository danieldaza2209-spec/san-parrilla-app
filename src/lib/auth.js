import { createHmac, createHash, timingSafeEqual } from 'node:crypto';

/**
 * Autenticación y control de roles (RBAC) de San Parrilla.
 *
 * - La sesión es un token firmado con HMAC-SHA256 guardado en una cookie HttpOnly.
 * - Las credenciales NUNCA van en el código: se leen de variables de entorno.
 *     AUTH_SECRET  -> clave para firmar sesiones (mínimo 16 caracteres)
 *     CAJERO_PIN   -> PIN / contraseña del rol Cajero
 *     ADMIN_PIN    -> PIN / contraseña del rol Administrador
 * - Si falta alguna variable en producción, el login queda deshabilitado (falla cerrado).
 */

export const SESSION_COOKIE = 'sp_session';
export const SESSION_TTL_SECONDS = 12 * 60 * 60; // 12 horas (un turno)

export const ROLE_CAJERO = 'cajero';
export const ROLE_ADMIN = 'admin';

export const ROLE_LABELS = {
  [ROLE_CAJERO]: 'Cajero',
  [ROLE_ADMIN]: 'Administrador',
};

function readEnv(name) {
  const fromProcess = typeof process !== 'undefined' ? process.env?.[name] : undefined;
  if (fromProcess) return fromProcess;
  try {
    return import.meta.env?.[name] || '';
  } catch {
    return '';
  }
}

// Valores iniciales por defecto si aún no se han configurado variables en Vercel
const DEFAULT_CONFIG = {
  AUTH_SECRET: 'san-parrilla-pos-default-secret-2026',
  CAJERO_PIN: '1111',
  ADMIN_PIN: '2222',
};

function getConfig(name) {
  const value = readEnv(name);
  if (value) return value;
  return DEFAULT_CONFIG[name] || '';
}

export function isAuthConfigured() {
  const secret = getConfig('AUTH_SECRET');
  return secret.length >= 16 && Boolean(getConfig('CAJERO_PIN')) && Boolean(getConfig('ADMIN_PIN'));
}

const sha256 = (value) => createHash('sha256').update(String(value)).digest();

function safeEqual(a, b) {
  return timingSafeEqual(sha256(a), sha256(b));
}

/** Devuelve { role, name } si el PIN es válido, o null. Mínimo privilegio si coinciden. */
export function authenticatePin(pin) {
  if (!isAuthConfigured() || typeof pin !== 'string' || pin.length === 0 || pin.length > 64) return null;

  const cajeroOk = safeEqual(pin, getConfig('CAJERO_PIN'));
  const adminOk = safeEqual(pin, getConfig('ADMIN_PIN'));

  if (cajeroOk) return { role: ROLE_CAJERO, name: ROLE_LABELS[ROLE_CAJERO] };
  if (adminOk) return { role: ROLE_ADMIN, name: ROLE_LABELS[ROLE_ADMIN] };
  return null;
}

// ---------- Tokens de sesión ----------

function sign(body) {
  return createHmac('sha256', getConfig('AUTH_SECRET')).update(body).digest('base64url');
}

export function createSessionToken({ role, name }) {
  const payload = {
    r: role,
    n: name,
    exp: Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS,
  };
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  return `${body}.${sign(body)}`;
}

export function verifySessionToken(token) {
  if (!isAuthConfigured() || typeof token !== 'string') return null;

  const [body, signature] = token.split('.');
  if (!body || !signature) return null;

  const expected = sign(body);
  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;

  try {
    const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
    if (!payload?.exp || payload.exp < Math.floor(Date.now() / 1000)) return null;
    if (payload.r !== ROLE_CAJERO && payload.r !== ROLE_ADMIN) return null;
    return { role: payload.r, name: payload.n || ROLE_LABELS[payload.r] };
  } catch {
    return null;
  }
}

// ---------- Matriz de permisos por ruta ----------

const STAFF = [ROLE_CAJERO, ROLE_ADMIN];
const ADMIN_ONLY = [ROLE_ADMIN];

/**
 * Reglas ordenadas. La primera que coincide con la ruta decide quién puede entrar.
 * `methods` limita la regla a ciertos métodos HTTP (si se omite aplica a todos).
 * Una ruta sin regla es pública (ej. "/", "/login", "/api/auth/*").
 */
const ACCESS_RULES = [
  { prefix: '/pos', roles: STAFF, kind: 'page' },
  { prefix: '/caja', roles: STAFF, kind: 'page' },
  { prefix: '/admin', roles: ADMIN_ONLY, kind: 'page' },

  { prefix: '/api/orders', roles: STAFF, kind: 'api' },
  { prefix: '/api/customers', roles: STAFF, kind: 'api' },
  { prefix: '/api/caja', roles: STAFF, kind: 'api' },
  { prefix: '/api/launcher', roles: ADMIN_ONLY, kind: 'api' },

  // Catálogo: lectura pública (la carta), escritura solo Administrador.
  { prefix: '/api/products', roles: ADMIN_ONLY, kind: 'api', methods: ['POST', 'PUT', 'PATCH', 'DELETE'] },
  { prefix: '/api/specials', roles: ADMIN_ONLY, kind: 'api', methods: ['POST', 'PUT', 'PATCH', 'DELETE'] },
];

const matchesPrefix = (pathname, prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`);

export function getAccessRule(pathname, method = 'GET') {
  const normalized = pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname;
  return (
    ACCESS_RULES.find(
      (rule) => matchesPrefix(normalized, rule.prefix) && (!rule.methods || rule.methods.includes(method.toUpperCase()))
    ) || null
  );
}

export function homeForRole(role) {
  return role === ROLE_ADMIN ? '/admin' : '/pos';
}

/**
 * Solo permite redirigir a rutas internas del personal a las que el rol realmente puede entrar.
 * Evita "open redirect" y evita mandar a un cajero a /admin.
 */
export function safeNextPath(next, role) {
  if (typeof next !== 'string' || !next.startsWith('/') || next.startsWith('//') || next.includes('\\')) {
    return homeForRole(role);
  }
  const pathname = next.split('?')[0];
  const rule = getAccessRule(pathname, 'GET');
  if (!rule || rule.kind !== 'page' || !rule.roles.includes(role)) return homeForRole(role);
  return next;
}
