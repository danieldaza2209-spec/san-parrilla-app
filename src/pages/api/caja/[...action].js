import { proxyToFastAPI } from '../../../lib/fastapi.js';
import { fetchActiveCajaFromNeon } from '../../../lib/neon.js';

export const prerender = false;

export async function ALL({ request, params }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const method = request.method.toUpperCase();

  if (action.startsWith('pay/')) {
    const pedidoId = action.slice(4).split('/')[0];
    return proxyToFastAPI(request, `/api/caja/pay/${pedidoId}`);
  }

  if (method === 'GET' && action === 'active') {
    const res = await proxyToFastAPI(request, '/api/caja/active');
    if (res.ok) return res;

    try {
      const neonCaja = await fetchActiveCajaFromNeon(3000);
      return new Response(JSON.stringify(neonCaja), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, max-age=0',
        },
      });
    } catch (_) {}
    return res;
  }

  const targetPath = action ? `/api/caja/${action}` : '/api/caja';
  return proxyToFastAPI(request, targetPath);
}
