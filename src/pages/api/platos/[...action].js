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
    const mapped = prods.map((p) => ({
      id: p.id,
      nombre: p.name,
      descripcion: p.category,
      precio: Number(p.price || 0),
      activo: Boolean(p.in_stock),
      disponible: Boolean(p.in_stock),
      categoria_id: p.menu_type === 'rapidas' ? 20 : 1,
    }));
    return new Response(JSON.stringify(mapped), { status: 200, headers: JSON_HEADERS });
  }

  if ((method === 'PUT' || method === 'PATCH' || method === 'POST') && parsedBody) {
    const id = Number(action) || Number(parsedBody.id);
    if (id && parsedBody.precio !== undefined) {
      updateProductPrice(id, Number(parsedBody.precio));
    }
    if (id && (parsedBody.disponible !== undefined || parsedBody.activo !== undefined)) {
      const disp = parsedBody.disponible !== undefined ? parsedBody.disponible : parsedBody.activo;
      toggleProductStock(id, Boolean(disp));
    }
    return new Response(
      JSON.stringify({
        id: id || 0,
        nombre: parsedBody.nombre || '',
        precio: Number(parsedBody.precio || 0),
        disponible: parsedBody.disponible !== undefined ? Boolean(parsedBody.disponible) : true,
        activo: parsedBody.disponible !== undefined ? Boolean(parsedBody.disponible) : true,
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
