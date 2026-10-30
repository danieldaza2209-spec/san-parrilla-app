import { fetchFastapi } from '../../../lib/fastapi.js';
import { getCustomerByPhone, searchCustomers, getAllCustomers, upsertCustomer } from '../../../lib/db.js';

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

  const targetPath = action ? `/api/clientes/${action}${search}` : `/api/clientes/${search}`;

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
      // Sincronizar también en SQLite local si es creación/actualización
      if ((method === 'POST' || method === 'PUT') && parsedBody && !action.includes('liquidar')) {
        try {
          const phone = parsedBody.telefono || parsedBody.phone;
          const name = parsedBody.nombre || parsedBody.name;
          const address = parsedBody.direccion || parsedBody.address || '';
          const notes = parsedBody.barrio || parsedBody.notas || parsedBody.notes || '';
          if (phone && name) {
            upsertCustomer(String(phone).trim(), String(name).trim(), String(address).trim(), String(notes).trim());
          }
        } catch (_) {}
      }
      return new Response(text || '[]', {
        status: upstream.status,
        headers: JSON_HEADERS,
      });
    }
  } catch (_) {
    // Fallback a SQLite local si el backend de FastAPI no responde temporalmente
  }

  // Fallback local
  if (method === 'GET') {
    const q = url.searchParams.get('q') || url.searchParams.get('search') || '';
    const phone = url.searchParams.get('telefono') || url.searchParams.get('phone') || '';
    if (phone) {
      const cust = getCustomerByPhone(phone.trim());
      const arr = cust
        ? [{
            id: cust.id,
            nombre: cust.name,
            name: cust.name,
            telefono: cust.phone,
            phone: cust.phone,
            direccion: cust.address,
            address: cust.address,
            barrio: cust.notes,
            notas: cust.notes,
            total_pedidos: cust.order_count || 0,
            order_count: cust.order_count || 0,
          }]
        : [];
      return new Response(JSON.stringify(arr), { status: 200, headers: JSON_HEADERS });
    }
    const list = q.trim() ? searchCustomers(q.trim()) : getAllCustomers();
    const mapped = (list || []).map((c) => ({
      id: c.id,
      nombre: c.name || c.nombre,
      name: c.name || c.nombre,
      telefono: c.phone || c.telefono,
      phone: c.phone || c.telefono,
      direccion: c.address || c.direccion || '',
      address: c.address || c.direccion || '',
      barrio: c.notes || c.barrio || '',
      notas: c.notes || c.notas || '',
      total_pedidos: c.order_count || 0,
      order_count: c.order_count || 0,
    }));
    return new Response(JSON.stringify(mapped), { status: 200, headers: JSON_HEADERS });
  }

  if ((method === 'POST' || method === 'PUT') && parsedBody) {
    const phone = String(parsedBody.telefono || parsedBody.phone || '').trim();
    const name = String(parsedBody.nombre || parsedBody.name || '').trim();
    const address = String(parsedBody.direccion || parsedBody.address || '').trim();
    const barrio = String(parsedBody.barrio || parsedBody.notas || parsedBody.notes || '').trim();
    if (phone && name) {
      const saved = upsertCustomer(phone, name, address, barrio);
      return new Response(
        JSON.stringify({
          id: saved?.id || Date.now(),
          nombre: name,
          name,
          telefono: phone,
          phone,
          direccion: address,
          address,
          barrio,
          notas: barrio,
        }),
        { status: 200, headers: JSON_HEADERS }
      );
    }
  }

  return new Response(JSON.stringify({ error: 'No se pudo procesar la solicitud de clientes.' }), {
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
