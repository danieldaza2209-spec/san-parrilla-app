import { getCustomerByPhone, searchCustomers, getAllCustomers, upsertCustomer } from '../../lib/db.js';
import { fetchFastapi } from '../../lib/fastapi.js';

export const prerender = false;

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store, no-cache, must-revalidate',
};

// GET /api/customers?phone=3001234567 OR ?q=searchterm
export async function GET({ url }) {
  const phone = url.searchParams.get('phone') || url.searchParams.get('telefono');
  const q = url.searchParams.get('q') || url.searchParams.get('search');

  try {
    const qs = new URLSearchParams();
    if (q) qs.set('q', q);
    if (phone) qs.set('telefono', phone);
    const endpoint = q || phone ? `/api/clientes/search?${qs.toString()}` : '/api/clientes/';
    const upstream = await fetchFastapi(endpoint, { method: 'GET', timeoutMs: 8000 });
    if (upstream.ok) {
      const data = await upstream.json();
      const list = Array.isArray(data) ? data : [];
      if (phone && !q) {
        const first = list[0] || null;
        return new Response(
          JSON.stringify({
            customer: first
              ? {
                  ...first,
                  name: first.nombre || first.name,
                  phone: first.telefono || first.phone,
                  address: first.direccion || first.address || '',
                  notes: first.barrio || first.notas || first.notes || '',
                  order_count: first.total_pedidos || first.order_count || 0,
                }
              : null,
            customers: list,
          }),
          { status: 200, headers: JSON_HEADERS }
        );
      }
      return new Response(
        JSON.stringify({
          customers: list.map((c) => ({
            ...c,
            name: c.nombre || c.name,
            phone: c.telefono || c.phone,
            address: c.direccion || c.address || '',
            notes: c.barrio || c.notas || c.notes || '',
            order_count: c.total_pedidos || c.order_count || 0,
          })),
        }),
        { status: 200, headers: JSON_HEADERS }
      );
    }
  } catch (_) {}

  try {
    if (phone) {
      const customer = getCustomerByPhone(phone.trim());
      return new Response(JSON.stringify({ customer: customer || null }), {
        status: 200,
        headers: JSON_HEADERS,
      });
    }
    if (q && q.trim().length >= 1) {
      const customers = searchCustomers(q.trim());
      return new Response(JSON.stringify({ customers }), {
        status: 200,
        headers: JSON_HEADERS,
      });
    }
    const customers = getAllCustomers();
    return new Response(JSON.stringify({ customers }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message, customers: [] }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  }
}

// POST /api/customers — create or update customer in Neon + local SQLite
export async function POST({ request }) {
  try {
    const body = await request.json();
    const phone = String(body.phone || body.telefono || '').trim();
    const name = String(body.name || body.nombre || '').trim();
    const address = String(body.address || body.direccion || '').trim();
    const barrio = String(body.barrio || body.notes || body.notas || '').trim();

    if (!phone && !name) {
      return new Response(JSON.stringify({ error: 'Teléfono o nombre son obligatorios' }), {
        status: 400,
        headers: JSON_HEADERS,
      });
    }

    try {
      const upstream = await fetchFastapi('/api/clientes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre: name || `Cliente ${phone}`,
          telefono: phone,
          direccion: address,
          barrio,
          notas: barrio,
        }),
        timeoutMs: 8000,
      });
      if (upstream.ok) {
        const neonCust = await upstream.json();
        try {
          if (phone && name) upsertCustomer(phone, name, address, barrio);
        } catch (_) {}
        return new Response(
          JSON.stringify({
            success: true,
            customer: {
              ...neonCust,
              name: neonCust.nombre || name,
              phone: neonCust.telefono || phone,
              address: neonCust.direccion || address,
              notes: neonCust.barrio || neonCust.notas || barrio,
            },
          }),
          { status: 200, headers: JSON_HEADERS }
        );
      }
    } catch (_) {}

    const customer = upsertCustomer(phone, name || `Cliente ${phone}`, address, barrio);
    return new Response(JSON.stringify({ success: true, customer }), {
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
