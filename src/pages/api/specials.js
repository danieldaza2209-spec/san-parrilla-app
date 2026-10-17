import { getDailySpecials, updateDailySpecials } from '../../lib/db.js';

export async function GET() {
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

export async function POST({ request }) {
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
