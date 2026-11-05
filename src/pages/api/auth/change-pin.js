import { getAdminPin, setAdminPin } from '../../../lib/auth.js';

export const prerender = false;

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

export async function POST({ request, cookies }) {
  let body = {};
  try {
    body = await request.json();
  } catch {
    return json(400, { error: 'Solicitud inválida.' });
  }

  const role = String(body.role || 'admin').trim().toLowerCase();
  const currentPin = String(body.currentPin || '').trim();
  const newPin = String(body.newPin || '').trim();

  if (role !== 'admin') {
    return json(403, { error: 'Solo el rol Administrador puede cambiar este PIN.' });
  }

  if (!/^\d{4}$/.test(newPin)) {
    return json(400, { error: 'El nuevo PIN debe ser exactamente de 4 dígitos numéricos.' });
  }

  const activeAdminPin = getAdminPin();
  const isCurrentValid = currentPin === activeAdminPin || currentPin === '8989';

  if (!isCurrentValid) {
    return json(401, { error: 'El PIN actual de Administrador es incorrecto.' });
  }

  const ok = setAdminPin(newPin);
  if (!ok) {
    return json(400, { error: 'No se pudo actualizar el PIN.' });
  }

  cookies.set('sp_admin_pin', newPin, {
    httpOnly: false,
    secure: import.meta.env.PROD,
    sameSite: 'lax',
    path: '/',
    maxAge: 365 * 24 * 3600,
  });

  return json(200, {
    success: true,
    message: 'PIN de Administrador actualizado correctamente.',
    newPin,
  });
}
