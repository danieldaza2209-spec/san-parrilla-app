import { m as getPublicProducts, n as db } from '../../chunks/db_DQ5gn_aw.mjs';
export { renderers } from '../../renderers.mjs';

// GET es público (es la misma información de la carta). El POST lo restringe el middleware a rol Administrador.
async function GET() {
  try {
    const products = getPublicProducts();
    return new Response(JSON.stringify(products), {
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
    const { action, id, price, is_active } = body;

    if (action === 'update_price' && id && price !== undefined) {
      db.prepare('UPDATE products SET price = ? WHERE id = ?').run(Number(price), id);
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (action === 'toggle_active' && id && is_active !== undefined) {
      db.prepare('UPDATE products SET is_active = ? WHERE id = ?').run(is_active ? 1 : 0, id);
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify({ error: 'Acción no válida' }), {
      status: 400,
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
