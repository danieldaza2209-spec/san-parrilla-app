import { proxyToFastAPI } from '../../../lib/fastapi.js';

export async function ALL({ request, params }) {
  const action = params.action || '';
  const targetPath = action ? `/api/caja/${action}` : '/api/caja';
  return proxyToFastAPI(request, targetPath);
}
