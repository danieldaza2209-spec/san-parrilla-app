import { fetchFastapi } from '../../../lib/fastapi.js';
import { getAllProducts, updateProductPrice, toggleProductStock } from '../../../lib/db.js';

export const prerender = false;

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store, no-cache, must-revalidate',
};

async function handleRequest({ params, request, url }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const method = request.method.toUpperCase();
  const search = url.search || '';

  let rawBody = null;
  let parsedBody = null;
  if (method !== 'GET' && method !== 'HEAD') {
    rawBody = await request.text();
    try {
      parsedBody = rawBody ? JSON.parse(rawBody) : {};
    } catch (_) {
      parsedBody = {};
    }
  }

  const targetPath = action ? `/api/platos/${action}${search}` : `/api/platos/${search}`;

  try {
    const upstream = await fetchFastapi(targetPath, {
      method,
      headers: {
        'Content-Type': request.headers.get('content-type') || 'application/json',
        Accept: 'application/json',
      },
      body: rawBody && rawBody.length > 0 ? rawBody : undefined,
      timeoutMs: 12000,
    });

    const text = await upstream.text();
    if (upstream.ok) {
      return new Response(text || '[]', {
        status: upstream.status,
        headers: JSON_HEADERS,
      });
    }
  } catch (_) {
    // Fallback a SQLite local si FastAPI no responde
  }

  if (method === 'GET') {
    const prods = getAllProducts() || [];
    const mapped = prods.map((p) => {
      const isAct = p.is_active !== undefined ? Boolean(p.is_active) : (p.in_stock !== undefined ? Boolean(p.in_stock) : true);
      return {
        id: p.id,
        nombre: p.name,
        descripcion: p.category || p.description || '',
        precio: Number(p.price || 0),
        activo: isAct,
        disponible: isAct,
        categoria_id: p.menu_type === 'rapidas' ? 20 : 1,
      };
    });
    return new Response(JSON.stringify(mapped), { status: 200, headers: JSON_HEADERS });
  }

  if ((method === 'PUT' || method === 'PATCH' || method === 'POST') && parsedBody) {
    const id = action || String(parsedBody.id || '');
    const prods = getAllProducts() || [];
    const existing = prods.find((p) => String(p.id) === String(id));

    if (id && parsedBody.precio !== undefined) {
      updateProductPrice(id, Number(parsedBody.precio));
    }
    if (id && (parsedBody.disponible !== undefined || parsedBody.activo !== undefined)) {
      const disp = parsedBody.disponible !== undefined ? parsedBody.disponible : parsedBody.activo;
      toggleProductStock(id, Boolean(disp));
    }
    const finalDisp = parsedBody.disponible !== undefined
      ? Boolean(parsedBody.disponible)
      : (parsedBody.activo !== undefined ? Boolean(parsedBody.activo) : (existing?.is_active !== undefined ? Boolean(existing.is_active) : true));
    const finalPrice = parsedBody.precio !== undefined
      ? Number(parsedBody.precio)
      : (existing?.price !== undefined ? Number(existing.price) : 0);
    const finalName = parsedBody.nombre || (existing?.name || '');

    return new Response(
      JSON.stringify({
        id: id || 0,
        nombre: finalName,
        precio: finalPrice,
        disponible: finalDisp,
        activo: finalDisp,
      }),
      { status: 200, headers: JSON_HEADERS }
    );
  }

  return new Response(JSON.stringify({ error: 'No se pudo procesar la solicitud de platos.' }), {
    status: 502,
    headers: JSON_HEADERS,
  });
}

export async function GET(ctx) {
  return handleRequest(ctx);
}
export async function POST(ctx) {
  return handleRequest(ctx);
}
export async function PUT(ctx) {
  return handleRequest(ctx);
}
export async function PATCH(ctx) {
  return handleRequest(ctx);
}
