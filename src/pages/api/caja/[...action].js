import { proxyToFastAPI } from '../../../lib/fastapi.js';

export async function ALL({ request, params }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  if (action.startsWith('pay/')) {
    const pedidoId = action.slice(4).split('/')[0];
    return proxyToFastAPI(request, `/api/pedidos/${pedidoId}/pagar`);
  }
  const targetPath = action ? `/api/caja/${action}` : '/api/caja';
  return proxyToFastAPI(request, targetPath);
}
