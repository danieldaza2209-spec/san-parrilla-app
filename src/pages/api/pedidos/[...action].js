import { proxyToFastAPI } from '../../../lib/fastapi.js';
import { fetchPedidosFromNeon, fetchPlatosFromNeon } from '../../../lib/neon.js';

export const prerender = false;

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
};

let cachedPlatosMap = null;
let cachedPlatosAt = 0;

async function resolvePlatosMap() {
  const now = Date.now();
  if (cachedPlatosMap && now - cachedPlatosAt < 5 * 60 * 1000) {
    return cachedPlatosMap;
  }
  try {
    const platos = await fetchPlatosFromNeon(2500);
    if (Array.isArray(platos) && platos.length > 0) {
      const map = new Map();
      for (const p of platos) {
        if (p && p.nombre && p.id) {
          map.set(String(p.nombre).trim().toLowerCase(), Number(p.id));
        }
      }
      cachedPlatosMap = map;
      cachedPlatosAt = now;
      return map;
    }
  } catch (e) {}
  return cachedPlatosMap || new Map();
}

export async function ALL({ request, params, url }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const methodUpper = request.method.toUpperCase();

  // 1. Consulta directa de pedidos desde Neon DB (evita 502/504 de Render en Cuentas por Cobrar, Caja y Pedidos)
  if (methodUpper === 'GET' && !action) {
    const limit = Number(url.searchParams.get('limit') || 300);
    const estado = url.searchParams.get('estado') || null;
    try {
      const orders = await fetchPedidosFromNeon({ limit, estado }, 4500);
      return new Response(JSON.stringify(orders), {
        status: 200,
        headers: JSON_HEADERS,
      });
    } catch (err) {
      console.warn('Fallback proxy en GET /api/pedidos:', err.message || err);
    }
  }

  // 2. Creación o actualización de pedido con detalles: normalizar tipo y resolver plato_id real por nombre
  if (['POST', 'PUT', 'PATCH'].includes(methodUpper)) {
    try {
      const cloned = request.clone();
      const body = await cloned.json();
      if (body && typeof body === 'object' && (!action || Array.isArray(body.detalles))) {
        if (body.tipo === 'MESA') body.tipo = 'EN_MESA';
        if (!body.cliente_nombre && body.customer_name) {
          body.cliente_nombre = body.customer_name;
        } else if (!body.customer_name && body.cliente_nombre) {
          body.customer_name = body.cliente_nombre;
        }
        if (Array.isArray(body.detalles)) {
          const platosMap = await resolvePlatosMap();
          for (const det of body.detalles) {
            const nameKey = String(det.nombre_plato || det.name || '').trim().toLowerCase();
            if (nameKey && platosMap.has(nameKey)) {
              det.plato_id = platosMap.get(nameKey);
            } else if (!Number.isInteger(Number(det.plato_id)) || Number(det.plato_id) <= 0) {
              det.plato_id = 1;
            } else {
              det.plato_id = Number(det.plato_id);
            }
            if (!det.notas_item && det.notas) {
              det.notas_item = det.notas;
            }
          }
        }
        const newReq = new Request(request.url, {
          method: methodUpper,
          headers: request.headers,
          body: JSON.stringify(body),
        });
        const target = action ? `/api/pedidos/${action}` : '/api/pedidos/';
        return proxyToFastAPI(newReq, target);
      }
    } catch (e) {}
  }

  const targetPath = action ? `/api/pedidos/${action}` : '/api/pedidos/';
  return proxyToFastAPI(request, targetPath);
}
