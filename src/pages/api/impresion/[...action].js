import { proxyToFastAPI } from '../../../lib/fastapi.js';

export async function ALL({ request, params }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const targetPath = action ? `/api/impresion/${action}` : '/api/impresion';
  return proxyToFastAPI(request, targetPath);
}
