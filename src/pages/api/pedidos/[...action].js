import { proxyToFastAPI, getSanitizedFastapiUrl } from '../../../lib/fastapi.js';

let cachedPlatosMap = null;
let cachedPlatosAt = 0;

async function resolvePlatosMap() {
  const now = Date.now();
  if (cachedPlatosMap && now - cachedPlatosAt < 5 * 60 * 1000) {
    return cachedPlatosMap;
  }
  try {
    const baseUrl = getSanitizedFastapiUrl();
    const res = await fetch(`${baseUrl}/api/catalogo/platos`, {
      headers: { Accept: 'application/json' },
    });
    if (res.ok) {
      const platos = await res.json();
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
    }
  } catch (e) {}
  return cachedPlatosMap || new Map();
}

export async function ALL({ request, params }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');

  const methodUpper = request.method.toUpperCase();

  // Si es creación o actualización de pedido con detalles, normalizar tipo y resolver plato_id real por nombre
  if (['POST', 'PUT', 'PATCH'].includes(methodUpper)) {
    try {
      const cloned = request.clone();
      const body = await cloned.json();
      if (body && typeof body === 'object' && (!action || Array.isArray(body.detalles))) {
        if (body.tipo === 'MESA') body.tipo = 'EN_MESA';
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
