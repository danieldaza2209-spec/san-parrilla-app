import { getAllProducts, updateProductPrice, toggleProductStock } from '../../lib/db.js';
import { fetchFastapi } from '../../lib/fastapi.js';

export const prerender = false;

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store, no-cache, must-revalidate',
};

export async function GET() {
  try {
    const upstream = await fetchFastapi('/api/platos/', { method: 'GET', timeoutMs: 8000 });
    if (upstream.ok) {
      const platos = await upstream.json();
      const products = (Array.isArray(platos) ? platos : []).map((p) => ({
        id: p.id,
        name: p.nombre,
        nombre: p.nombre,
        category: p.descripcion || 'Menú San Parrilla',
        price: Number(p.precio || 0),
        precio: Number(p.precio || 0),
        in_stock: p.disponible !== false && p.activo !== false ? 1 : 0,
        disponible: p.disponible !== false && p.activo !== false,
        activo: p.activo !== false,
        categoria_id: p.categoria_id,
      }));
      return new Response(JSON.stringify({ products, platos }), {
        status: 200,
        headers: JSON_HEADERS,
      });
    }
  } catch (_) {}

  try {
    const products = getAllProducts();
    return new Response(JSON.stringify({ products }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message, products: [] }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  }
}

export async function PUT({ request }) {
  try {
    const body = await request.json();
    const id = Number(body.id);
    const nombre = body.nombre || body.name;
    const price = body.price !== undefined ? Number(body.price) : (body.precio !== undefined ? Number(body.precio) : undefined);
    const disponible =
      body.disponible !== undefined
        ? Boolean(body.disponible)
        : body.in_stock !== undefined
        ? Boolean(body.in_stock)
        : undefined;

    try {
      const targetEndpoint = nombre && !id ? '/api/platos/by-name' : `/api/platos/${id}`;
      const upstream = await fetchFastapi(targetEndpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre,
          precio: price,
          disponible,
          activo: disponible,
        }),
        timeoutMs: 8000,
      });
      if (upstream.ok) {
        const updated = await upstream.json();
        try {
          if (id && price !== undefined) updateProductPrice(id, price);
          if (id && disponible !== undefined) toggleProductStock(id, disponible);
        } catch (_) {}
        return new Response(JSON.stringify({ success: true, plato: updated }), {
          status: 200,
          headers: JSON_HEADERS,
        });
      }
    } catch (_) {}

    if (id && price !== undefined) {
      updateProductPrice(id, price);
    }
    if (id && disponible !== undefined) {
      toggleProductStock(id, disponible);
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: JSON_HEADERS,
    });
  }
}
