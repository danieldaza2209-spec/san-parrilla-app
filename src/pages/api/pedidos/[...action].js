import { proxyToFastAPI } from '../../../lib/fastapi.js';

export async function ALL({ request, params }) {
  const action = params.action || '';
  const targetPath = `/api/pedidos/${action}`;
  return proxyToFastAPI(request, targetPath);
}
