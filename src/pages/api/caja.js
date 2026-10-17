import { getActiveCashRegister, openCashRegister, closeCashRegister } from '../../lib/db.js';

export async function GET() {
  try {
    const cash = getActiveCashRegister();
    return new Response(JSON.stringify(cash || null), {
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
    const { action, initialCash, countedCash, notes } = body;

    if (action === 'open') {
      const reg = openCashRegister(Number(initialCash) || 0, notes || '');
      return new Response(JSON.stringify({ success: true, cashRegister: reg }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (action === 'close') {
      const active = getActiveCashRegister();
      if (!active) {
        return new Response(JSON.stringify({ error: 'No hay ninguna caja abierta' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      const closed = closeCashRegister(active.id, Number(countedCash) || 0, notes || '');
      return new Response(JSON.stringify({ success: true, cashRegister: closed }), {
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
