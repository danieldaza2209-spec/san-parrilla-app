import { searchCustomers, getCustomerByPhone, upsertCustomer } from '../../lib/db.js';

export async function GET({ url }) {
  try {
    const phone = url.searchParams.get('phone');
    if (phone) {
      const customer = getCustomerByPhone(phone);
      return new Response(JSON.stringify(customer || null), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const query = url.searchParams.get('q') || '';
    const customers = searchCustomers(query);
    return new Response(JSON.stringify(customers), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

export async function POST({ request }) {
  try {
    const body = await request.json();
    if (!body.phone || !body.name || !body.address) {
      return new Response(JSON.stringify({ error: 'Nombre, teléfono y dirección son obligatorios' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const customer = upsertCustomer(body);
    return new Response(JSON.stringify({ success: true, customer }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
