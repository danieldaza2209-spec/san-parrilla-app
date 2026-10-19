import { timingSafeEqual, createHmac, createHash } from 'node:crypto';

const __vite_import_meta_env__ = {"ASSETS_PREFIX": undefined, "BASE_URL": "/", "DEV": false, "MODE": "production", "PROD": true, "SITE": undefined, "SSR": true};
const SESSION_COOKIE = "sp_session";
const SESSION_TTL_SECONDS = 12 * 60 * 60;
const ROLE_CAJERO = "cajero";
const ROLE_ADMIN = "admin";
const ROLE_LABELS = {
  [ROLE_CAJERO]: "Cajero",
  [ROLE_ADMIN]: "Administrador"
};
function readEnv(name) {
  const fromProcess = typeof process !== "undefined" ? process.env?.[name] : void 0;
  if (fromProcess) return fromProcess;
  try {
    return Object.assign(__vite_import_meta_env__, { _: process.env._ })?.[name] || "";
  } catch {
    return "";
  }
}
const DEFAULT_CONFIG = {
  AUTH_SECRET: "san-parrilla-pos-default-secret-2026",
  CAJERO_PIN: "1111",
  ADMIN_PIN: "2222"
};
function getConfig(name) {
  const value = readEnv(name);
  if (value) return value;
  return DEFAULT_CONFIG[name] || "";
}
function isAuthConfigured() {
  const secret = getConfig("AUTH_SECRET");
  return secret.length >= 16 && Boolean(getConfig("CAJERO_PIN")) && Boolean(getConfig("ADMIN_PIN"));
}
const sha256 = (value) => createHash("sha256").update(String(value)).digest();
function safeEqual(a, b) {
  return timingSafeEqual(sha256(a), sha256(b));
}
function authenticatePin(pin) {
  if (!isAuthConfigured() || typeof pin !== "string" || pin.length === 0 || pin.length > 64) return null;
  const cajeroOk = safeEqual(pin, getConfig("CAJERO_PIN"));
  const adminOk = safeEqual(pin, getConfig("ADMIN_PIN"));
  if (cajeroOk) return { role: ROLE_CAJERO, name: ROLE_LABELS[ROLE_CAJERO] };
  if (adminOk) return { role: ROLE_ADMIN, name: ROLE_LABELS[ROLE_ADMIN] };
  return null;
}
function sign(body) {
  return createHmac("sha256", getConfig("AUTH_SECRET")).update(body).digest("base64url");
}
function createSessionToken({ role, name }) {
  const payload = {
    r: role,
    n: name,
    exp: Math.floor(Date.now() / 1e3) + SESSION_TTL_SECONDS
  };
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${body}.${sign(body)}`;
}
function verifySessionToken(token) {
  if (!isAuthConfigured() || typeof token !== "string") return null;
  const [body, signature] = token.split(".");
  if (!body || !signature) return null;
  const expected = sign(body);
  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  try {
    const payload = JSON.parse(Buffer.from(body, "base64url").toString("utf8"));
    if (!payload?.exp || payload.exp < Math.floor(Date.now() / 1e3)) return null;
    if (payload.r !== ROLE_CAJERO && payload.r !== ROLE_ADMIN) return null;
    return { role: payload.r, name: payload.n || ROLE_LABELS[payload.r] };
  } catch {
    return null;
  }
}
const STAFF = [ROLE_CAJERO, ROLE_ADMIN];
const ADMIN_ONLY = [ROLE_ADMIN];
const ACCESS_RULES = [
  { prefix: "/pos", roles: STAFF, kind: "page" },
  { prefix: "/caja", roles: STAFF, kind: "page" },
  { prefix: "/admin", roles: ADMIN_ONLY, kind: "page" },
  { prefix: "/api/orders", roles: STAFF, kind: "api" },
  { prefix: "/api/customers", roles: STAFF, kind: "api" },
  { prefix: "/api/caja", roles: STAFF, kind: "api" },
  { prefix: "/api/launcher", roles: ADMIN_ONLY, kind: "api" },
  // Catálogo: lectura pública (la carta), escritura solo Administrador.
  { prefix: "/api/products", roles: ADMIN_ONLY, kind: "api", methods: ["POST", "PUT", "PATCH", "DELETE"] },
  { prefix: "/api/specials", roles: ADMIN_ONLY, kind: "api", methods: ["POST", "PUT", "PATCH", "DELETE"] }
];
const matchesPrefix = (pathname, prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`);
function getAccessRule(pathname, method = "GET") {
  const normalized = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  return ACCESS_RULES.find(
    (rule) => matchesPrefix(normalized, rule.prefix) && (!rule.methods || rule.methods.includes(method.toUpperCase()))
  ) || null;
}
function homeForRole(role) {
  return role === ROLE_ADMIN ? "/admin" : "/pos";
}
function safeNextPath(next, role) {
  if (typeof next !== "string" || !next.startsWith("/") || next.startsWith("//") || next.includes("\\")) {
    return homeForRole(role);
  }
  const pathname = next.split("?")[0];
  const rule = getAccessRule(pathname, "GET");
  if (!rule || rule.kind !== "page" || !rule.roles.includes(role)) return homeForRole(role);
  return next;
}

export { ROLE_ADMIN as R, SESSION_COOKIE as S, authenticatePin as a, SESSION_TTL_SECONDS as b, createSessionToken as c, ROLE_LABELS as d, getAccessRule as g, homeForRole as h, isAuthConfigured as i, safeNextPath as s, verifySessionToken as v };
