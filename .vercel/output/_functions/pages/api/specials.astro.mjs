import { a as getDailySpecials, l as updateDailySpecials } from '../../chunks/db_DvolSJbv.mjs';
export { renderers } from '../../renderers.mjs';

async function GET() {
  try {
    const specials = getDailySpecials();
    return new Response(JSON.stringify(specials), {
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
    const { sopa, principios, acompanamientos } = body;
    if (!sopa || !principios || !acompanamientos) {
      return new Response(JSON.stringify({ error: 'Faltan campos requeridos' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    updateDailySpecials(sopa, principios, acompanamientos);
    return new Response(JSON.stringify({ success: true, specials: getDailySpecials() }), {
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
