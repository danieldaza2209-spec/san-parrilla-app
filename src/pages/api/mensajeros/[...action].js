import { proxyToFastAPI } from '../../../lib/fastapi.js';
import { fetchMensajerosFromNeon } from '../../../lib/neon.js';

export const prerender = false;

const DEFAULT_MENSAJEROS = [
  { id: 1, nombre: 'Luseli', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 2, nombre: 'Freddy', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 3, nombre: 'Mauricio', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 4, nombre: 'Henry', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 5, nombre: 'Mensajería USA', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 6, nombre: 'Jefferson', telefono: null, activo: true, creado_en: new Date().toISOString() },
];

export async function ALL({ request, params, url }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const methodUpper = request.method.toUpperCase();

  if (methodUpper === 'GET' && !action) {
    const incluirInactivos = url.searchParams.get('incluir_inactivos') === 'true';
    try {
      const rows = await fetchMensajerosFromNeon({ incluirInactivos }, 3000);
      if (Array.isArray(rows) && rows.length > 0) {
        return new Response(JSON.stringify(rows), {
          status: 200,
          headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
        });
      }
    } catch (_) {}

    const fallbackList = incluirInactivos
      ? DEFAULT_MENSAJEROS
      : DEFAULT_MENSAJEROS.filter((m) => m.activo);
    return new Response(JSON.stringify(fallbackList), {
      status: 200,
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    });
  }

  const targetPath = action ? `/api/mensajeros/${action}` : '/api/mensajeros';
  return proxyToFastAPI(request, targetPath);
}
