import { proxyToFastAPI } from '../../../lib/fastapi.js';

export const prerender = false;

const DEFAULT_MENSAJEROS = [
  { id: 1, nombre: 'Luseli', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 2, nombre: 'Freddy', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 3, nombre: 'Mauricio', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 4, nombre: 'Henry', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 5, nombre: 'Mensajería USA', telefono: null, activo: true, creado_en: new Date().toISOString() },
  { id: 6, nombre: 'Jefferson', telefono: null, activo: true, creado_en: new Date().toISOString() },
];

export async function ALL({ request, params }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const targetPath = action ? `/api/mensajeros/${action}` : '/api/mensajeros';

  return proxyToFastAPI(request, targetPath, {
    fallback: () => {
      const methodUpper = request.method.toUpperCase();
      if (methodUpper === 'GET') {
        const url = new URL(request.url);
        const incluirInactivos = url.searchParams.get('incluir_inactivos') === 'true';
        if (incluirInactivos) return DEFAULT_MENSAJEROS;
        return DEFAULT_MENSAJEROS.filter((m) => m.activo);
      }
      return DEFAULT_MENSAJEROS;
    },
  });
}
