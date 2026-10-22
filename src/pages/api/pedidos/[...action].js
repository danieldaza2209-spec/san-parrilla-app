import { proxyToFastAPI } from '../../../lib/fastapi.js';

export async function ALL({ request, params }) {
  const action = params.action || '';
  const targetPath = action ? `/api/pedidos/${action}` : '/api/pedidos/';
  return proxyToFastAPI(request, targetPath);
}
