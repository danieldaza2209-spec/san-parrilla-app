import { h as getOrderDetails, i as getRecentOrders, j as createOrder } from '../../chunks/db_CYyknqGr.mjs';
export { renderers } from '../../renderers.mjs';

async function GET({ url }) {
  try {
    const id = url.searchParams.get('id');
    if (id) {
      const order = getOrderDetails(Number(id));
      if (!order) {
        return new Response(JSON.stringify({ error: 'Pedido no encontrado' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      return new Response(JSON.stringify(order), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const limit = Number(url.searchParams.get('limit')) || 30;
    const orders = getRecentOrders(limit);
    return new Response(JSON.stringify(orders), {
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
    const { orderData, items } = body;

    if (!orderData || !items || items.length === 0) {
      return new Response(JSON.stringify({ error: 'Datos de pedido o productos incompletos' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const order = createOrder(orderData, items);
    return new Response(JSON.stringify({ success: true, order }), {
      status: 201,
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
