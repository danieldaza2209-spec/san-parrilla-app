import { b as getProducts, k as db } from '../../chunks/db_CYyknqGr.mjs';
export { renderers } from '../../renderers.mjs';

async function GET({ url }) {
  try {
    const all = url.searchParams.get('all') === 'true';
    const products = getProducts(!all);
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
