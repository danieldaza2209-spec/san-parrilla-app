import {
  SESSION_COOKIE,
  SESSION_TTL_SECONDS,
  authenticatePin,
  createSessionToken,
  isAuthConfigured,
  safeNextPath,
} from '../../../lib/auth.js';

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

// Freno básico contra fuerza bruta: 5 fallos por IP cada 10 minutos.
// (En memoria: protege por instancia; suficiente junto con PINs no triviales.)
const MAX_FAILS = 5;
const WINDOW_MS = 10 * 60 * 1000;
const attempts = new Map();

function clientKey(request) {
  return (request.headers.get('x-forwarded-for') || 'local').split(',')[0].trim();
}

function isBlocked(key) {
  const entry = attempts.get(key);
  if (!entry) return false;
  if (Date.now() - entry.first > WINDOW_MS) {
    attempts.delete(key);
    return false;
  }
  return entry.count >= MAX_FAILS;
}

function registerFail(key) {
  const entry = attempts.get(key);
  if (!entry || Date.now() - entry.first > WINDOW_MS) {
    attempts.set(key, { count: 1, first: Date.now() });
  } else {
    entry.count += 1;
  }
}

export async function POST({ request, cookies }) {
  if (!isAuthConfigured()) {
    return json(503, { error: 'El acceso del personal aún no está configurado en el servidor.' });
  }

  const key = clientKey(request);
  if (isBlocked(key)) {
    return json(429, { error: 'Demasiados intentos. Espera unos minutos e inténtalo de nuevo.' });
  }

  let body = {};
  try {
    body = await request.json();
  } catch {
    return json(400, { error: 'Solicitud inválida.' });
  }

  const user = authenticatePin(String(body.pin ?? '').trim());
  if (!user) {
    registerFail(key);
    await new Promise((resolve) => setTimeout(resolve, 400)); // enlentece adivinar PINs
    return json(401, { error: 'PIN o contraseña incorrectos.' });
  }

  attempts.delete(key);
  cookies.set(SESSION_COOKIE, createSessionToken(user), {
    httpOnly: true,
    secure: import.meta.env.PROD,
    sameSite: 'lax',
    path: '/',
    maxAge: SESSION_TTL_SECONDS,
  });

  return json(200, {
    success: true,
    role: user.role,
    redirect: safeNextPath(body.next, user.role),
  });
}
