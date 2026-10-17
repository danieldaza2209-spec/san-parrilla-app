import { f as getCustomerByPhone, s as searchCustomers, u as upsertCustomer } from '../../chunks/db_DvolSJbv.mjs';
export { renderers } from '../../renderers.mjs';

async function GET({ url }) {
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

async function POST({ request }) {
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

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  GET,
  POST
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
