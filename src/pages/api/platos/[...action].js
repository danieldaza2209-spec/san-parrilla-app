import { fetchFastapi } from '../../../lib/fastapi.js';
import { getAllProducts, updateProductPrice, toggleProductStock } from '../../../lib/db.js';

export const prerender = false;

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store, no-cache, must-revalidate',
};

const normText = (str) =>
  String(str || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

const CALIBRATED_BEBIDAS = [
  { key: 'botella de agua', nombre: 'Botella de Agua', precio: 3000, legacyPrices: [0] },
  { key: 'cerveza club colombia / aguila', nombre: 'Cerveza Club Colombia / Águila', precio: 5500, legacyPrices: [0, 4500] },
  { key: 'gaseosa 1.5l', nombre: 'Gaseosa 1.5L', precio: 8000, legacyPrices: [0] },
  { key: 'gaseosa 400ml', nombre: 'Gaseosa 400ml', precio: 4000, legacyPrices: [0] },
  { key: 'jugo natural en agua', nombre: 'Jugo Natural en Agua', precio: 8500, legacyPrices: [0, 6000] },
  { key: 'jugo natural en leche', nombre: 'Jugo Natural en Leche', precio: 9500, legacyPrices: [0, 7500] },
  { key: 'soda', nombre: 'Soda', precio: 4500, legacyPrices: [0] },
  { key: 'porcion de papas a la francesa', nombre: 'Porción de Papas a la Francesa', precio: 5500, legacyPrices: [0, 6000] },
];

const REQUIRED_18K_DISHES = [
  { key: 'arroz con pollo', nombre: 'Arroz con pollo', precio: 18000 },
  { key: 'espagueti con pollo', nombre: 'Espagueti con pollo', precio: 18000 },
  { key: 'arroz campesino', nombre: 'Arroz campesino', precio: 18000 },
  { key: 'arroz mixto', nombre: 'Arroz mixto', precio: 18000 },
];

function sanitizeCatalogPlatos(rawList) {
  if (!Array.isArray(rawList)) return [];
  const byKey = new Map();

  for (const item of rawList) {
    if (!item || typeof item !== 'object') continue;
    let rawName = String(item.nombre || item.name || '').trim();
    if (!rawName) continue;

    let key = normText(rawName);
    // Eliminar por completo Porción de Patacón con Hogao
    if (key.includes('patacon con hogao')) continue;

    // Normalizar Espaguetis con pollo -> Espagueti con pollo (evitar duplicados en $18.000)
    if (key === 'espaguetis con pollo' || key === 'espagueti con pollo') {
      rawName = 'Espagueti con pollo';
      key = 'espagueti con pollo';
    } else if (key === 'botella de agua') {
      rawName = 'Botella de Agua';
    } else if (key === 'porcion de papas a la francesa' || key === 'papa francesa casera') {
      rawName = 'Porción de Papas a la Francesa';
      key = 'porcion de papas a la francesa';
    }

    let precio = Number(item.precio ?? item.price ?? 0);
    const calBeb = CALIBRATED_BEBIDAS.find((b) => b.key === key);
    if (calBeb) {
      rawName = calBeb.nombre;
      if (calBeb.legacyPrices.includes(Math.round(precio)) || precio <= 0) {
        precio = calBeb.precio;
      }
    }

    const isDisp =
      item.disponible !== undefined
        ? Boolean(item.disponible)
        : item.activo !== undefined
        ? Boolean(item.activo)
        : item.is_active !== undefined
        ? Boolean(item.is_active)
        : true;

    const normalizedItem = {
      ...item,
      nombre: rawName,
      precio,
      disponible: isDisp,
      activo: isDisp,
    };

    if (!byKey.has(key)) {
      byKey.set(key, normalizedItem);
    } else {
      // Si ya existe un registro (ej. duplicado de Espagueti con pollo o Papas a la Francesa), conservar solo 1
      const existing = byKey.get(key);
      // Preferir el registro cuyo nombre original ya era exacto o conservar el primero
      if (normText(item.nombre || '') === key && normText(existing.nombre || '') !== key) {
        byKey.set(key, normalizedItem);
      }
    }
  }

  // Asegurar que las bebidas calibradas existan en el catálogo
  for (const cal of CALIBRATED_BEBIDAS) {
    if (!byKey.has(cal.key)) {
      byKey.set(cal.key, {
        id: `beb-${cal.key.replace(/[^a-z0-9]/g, '-')}`,
        nombre: cal.nombre,
        descripcion: 'Bebidas y Adicionales',
        precio: cal.precio,
        disponible: true,
        activo: true,
        categoria_id: 6,
      });
    }
  }

  // Asegurar que los platos de $18.000 requeridos existan en el catálogo
  for (const req18 of REQUIRED_18K_DISHES) {
    if (!byKey.has(req18.key)) {
      byKey.set(req18.key, {
        id: `alm18-${req18.key.replace(/[^a-z0-9]/g, '-')}`,
        nombre: req18.nombre,
        descripcion: 'Platos Fuertes $18.000',
        precio: req18.precio,
        disponible: true,
        activo: true,
        categoria_id: 3,
      });
    }
  }

  return Array.from(byKey.values());
}

async function handleRequest({ params, request, url }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const method = request.method.toUpperCase();
  const search = url.search || '';

  let rawBody = null;
  let parsedBody = null;
  if (method !== 'GET' && method !== 'HEAD') {
    rawBody = await request.text();
    try {
      parsedBody = rawBody ? JSON.parse(rawBody) : {};
    } catch (_) {
      parsedBody = {};
    }
  }

  const targetPath = action ? `/api/platos/${action}${search}` : `/api/platos/${search}`;

  try {
    const upstream = await fetchFastapi(targetPath, {
      method,
      headers: {
        'Content-Type': request.headers.get('content-type') || 'application/json',
        Accept: 'application/json',
      },
      body: rawBody && rawBody.length > 0 ? rawBody : undefined,
      timeoutMs: 12000,
    });

    const text = await upstream.text();
    if (upstream.ok) {
      if (method === 'GET' && !action) {
        try {
          const parsed = JSON.parse(text || '[]');
          const sanitized = sanitizeCatalogPlatos(parsed);
          return new Response(JSON.stringify(sanitized), {
            status: 200,
            headers: JSON_HEADERS,
          });
        } catch (_) {}
      }

      // Si se actualizó Espagueti con pollo o Porción de Papas a la Francesa, sincronizar posibles duplicados por nombre en FastAPI
      if ((method === 'PUT' || method === 'PATCH') && parsedBody) {
        try {
          const updatedObj = JSON.parse(text || '{}');
          const nKey = normText(updatedObj.nombre || parsedBody.nombre || '');
          if (nKey === 'espagueti con pollo' || nKey === 'espaguetis con pollo') {
            for (const variantName of ['Espagueti con pollo', 'Espaguetis con pollo']) {
              await fetchFastapi(`/api/platos/by-name?nombre=${encodeURIComponent(variantName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify({
                  nombre: 'Espagueti con pollo',
                  precio: updatedObj.precio ?? parsedBody.precio,
                  disponible: updatedObj.disponible ?? parsedBody.disponible,
                  activo: updatedObj.activo ?? parsedBody.activo ?? parsedBody.disponible,
                }),
                timeoutMs: 5000,
              }).catch(() => {});
            }
          }
        } catch (_) {}
      }

      return new Response(text || '[]', {
        status: upstream.status,
        headers: JSON_HEADERS,
      });
    }
  } catch (_) {
    // Fallback a SQLite local si FastAPI no responde
  }

  if (method === 'GET') {
    const prods = getAllProducts() || [];
    const mapped = prods.map((p) => {
      const isAct = p.is_active !== undefined ? Boolean(p.is_active) : (p.in_stock !== undefined ? Boolean(p.in_stock) : true);
      return {
        id: p.id,
        nombre: p.name,
        descripcion: p.category || p.description || '',
        precio: Number(p.price || 0),
        activo: isAct,
        disponible: isAct,
        categoria_id: p.menu_type === 'rapidas' ? 20 : 1,
      };
    });
    return new Response(JSON.stringify(sanitizeCatalogPlatos(mapped)), { status: 200, headers: JSON_HEADERS });
  }

  if ((method === 'PUT' || method === 'PATCH' || method === 'POST') && parsedBody) {
    const id = action || String(parsedBody.id || '');
    const prods = getAllProducts() || [];
    const existing = prods.find((p) => String(p.id) === String(id));

    if (id && parsedBody.precio !== undefined) {
      updateProductPrice(id, Number(parsedBody.precio));
    }
    if (id && (parsedBody.disponible !== undefined || parsedBody.activo !== undefined)) {
      const disp = parsedBody.disponible !== undefined ? parsedBody.disponible : parsedBody.activo;
      toggleProductStock(id, Boolean(disp));
    }
    const finalDisp = parsedBody.disponible !== undefined
      ? Boolean(parsedBody.disponible)
      : (parsedBody.activo !== undefined ? Boolean(parsedBody.activo) : (existing?.is_active !== undefined ? Boolean(existing.is_active) : true));
    const finalPrice = parsedBody.precio !== undefined
      ? Number(parsedBody.precio)
      : (existing?.price !== undefined ? Number(existing.price) : 0);
    const finalName = parsedBody.nombre || (existing?.name || '');

    return new Response(
      JSON.stringify({
        id: id || 0,
        nombre: finalName,
        precio: finalPrice,
        disponible: finalDisp,
        activo: finalDisp,
      }),
      { status: 200, headers: JSON_HEADERS }
    );
  }

  return new Response(JSON.stringify({ error: 'No se pudo procesar la solicitud de platos.' }), {
    status: 502,
    headers: JSON_HEADERS,
  });
}

export async function GET(ctx) {
  return handleRequest(ctx);
}
export async function POST(ctx) {
  return handleRequest(ctx);
}
export async function PUT(ctx) {
  return handleRequest(ctx);
}
export async function PATCH(ctx) {
  return handleRequest(ctx);
}
