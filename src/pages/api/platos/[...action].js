import {
  getAllProducts,
  updateProductPrice,
  toggleProductStock,
  setDishOverride,
  getDishOverrides,
} from '../../../lib/db.js';
import {
  fetchPlatosFromNeon,
  pullOverridesFromNeon,
  pushOverridesToNeon,
  updateSinglePlatoInNeon,
  bulkUpdatePlatosPriceInNeon,
} from '../../../lib/neon.js';

export const prerender = false;

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
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

export function sanitizeCatalogPlatos(rawList, overridesMap = {}) {
  if (!Array.isArray(rawList)) return [];
  const activeOverrides = { ...getDishOverrides(), ...(overridesMap || {}) };
  const byKey = new Map();

  for (const item of rawList) {
    if (!item || typeof item !== 'object') continue;
    let rawName = String(item.nombre || item.name || '').trim();
    if (!rawName) continue;

    let key = normText(rawName);
    if (key.includes('patacon con hogao')) continue;

    let precio = Number(item.precio ?? item.price ?? 0);

    if (key === 'espaguetis con pollo' || key === 'espagueti con pollo') {
      rawName = 'Espagueti con pollo';
      key = 'espagueti con pollo';
    } else if (key === 'botella de agua' || key === 'agua') {
      rawName = 'Botella de Agua';
      key = 'botella de agua';
    } else if (
      key === 'porcion de papas a la francesa' ||
      key === 'papa francesa casera' ||
      key === 'porcion de papa a la francesa'
    ) {
      rawName = 'Porción de Papas a la Francesa';
      key = 'porcion de papas a la francesa';
    } else if (key === 'picada por uno' || key === 'picada por 1' || key === 'picada x 1') {
      rawName = 'Picada x 1';
      key = 'picada x 1';
      if (precio === 19500 || precio <= 0) {
        precio = 27500;
      }
    }

    const calBeb = CALIBRATED_BEBIDAS.find((b) => b.key === key);
    if (calBeb) {
      rawName = calBeb.nombre;
      if (calBeb.legacyPrices.includes(Math.round(precio)) || precio <= 0) {
        precio = calBeb.precio;
      }
    }

    let isDisp =
      item.disponible !== undefined
        ? Boolean(item.disponible)
        : item.activo !== undefined
        ? Boolean(item.activo)
        : item.is_active !== undefined
        ? Boolean(item.is_active)
        : true;

    const ovr = activeOverrides[key] || activeOverrides[normText(item.id)];
    if (ovr) {
      if (ovr.disponible !== undefined) isDisp = Boolean(ovr.disponible);
      if (ovr.precio !== undefined && Number(ovr.precio) > 0) precio = Number(ovr.precio);
    }

    const normalizedItem = {
      ...item,
      nombre: rawName,
      name: rawName,
      precio,
      price: precio,
      disponible: isDisp,
      activo: isDisp,
      is_active: isDisp ? 1 : 0,
      in_stock: isDisp ? 1 : 0,
    };

    if (!byKey.has(key)) {
      byKey.set(key, normalizedItem);
    } else {
      const existing = byKey.get(key);
      const mergedDisp = ovr?.disponible !== undefined ? Boolean(ovr.disponible) : existing.disponible && isDisp;
      const preferred =
        normText(item.nombre || '') === key && normText(existing.nombre || '') !== key ? normalizedItem : existing;
      byKey.set(key, {
        ...preferred,
        disponible: mergedDisp,
        activo: mergedDisp,
        is_active: mergedDisp ? 1 : 0,
        in_stock: mergedDisp ? 1 : 0,
      });
    }
  }

  for (const cal of CALIBRATED_BEBIDAS) {
    if (!byKey.has(cal.key)) {
      const ovr = activeOverrides[cal.key];
      const isDisp = ovr?.disponible !== undefined ? Boolean(ovr.disponible) : true;
      const precio = ovr?.precio !== undefined && Number(ovr.precio) > 0 ? Number(ovr.precio) : cal.precio;
      byKey.set(cal.key, {
        id: `beb-${cal.key.replace(/[^a-z0-9]/g, '-')}`,
        nombre: cal.nombre,
        name: cal.nombre,
        descripcion: 'Bebidas y Adicionales',
        precio,
        price: precio,
        disponible: isDisp,
        activo: isDisp,
        is_active: isDisp ? 1 : 0,
        in_stock: isDisp ? 1 : 0,
        categoria_id: 6,
      });
    }
  }

  for (const req18 of REQUIRED_18K_DISHES) {
    if (!byKey.has(req18.key)) {
      const ovr = activeOverrides[req18.key];
      const isDisp = ovr?.disponible !== undefined ? Boolean(ovr.disponible) : true;
      const precio = ovr?.precio !== undefined && Number(ovr.precio) > 0 ? Number(ovr.precio) : req18.precio;
      byKey.set(req18.key, {
        id: `alm18-${req18.key.replace(/[^a-z0-9]/g, '-')}`,
        nombre: req18.nombre,
        name: req18.nombre,
        descripcion: 'Platos Fuertes $18.000',
        precio,
        price: precio,
        disponible: isDisp,
        activo: isDisp,
        is_active: isDisp ? 1 : 0,
        in_stock: isDisp ? 1 : 0,
        categoria_id: 3,
      });
    }
  }

  return Array.from(byKey.values());
}

export function getFallbackSanitizedPlatos() {
  const prods = getAllProducts() || [];
  const mapped = prods.map((p) => {
    const isAct =
      p.disponible !== undefined
        ? Boolean(p.disponible)
        : p.is_active !== undefined
        ? Boolean(p.is_active)
        : true;
    return {
      id: p.id,
      nombre: p.name || p.nombre,
      name: p.name || p.nombre,
      descripcion: p.category || p.description || '',
      precio: Number(p.price ?? p.precio ?? 0),
      price: Number(p.price ?? p.precio ?? 0),
      activo: isAct,
      disponible: isAct,
      categoria_id: p.menu_type === 'rapidas' ? 20 : 1,
    };
  });
  return sanitizeCatalogPlatos(mapped, getDishOverrides());
}

export async function fetchLiveSanitizedPlatos() {
  try {
    const neonRows = await fetchPlatosFromNeon(3500);
    if (Array.isArray(neonRows) && neonRows.length > 0) {
      return sanitizeCatalogPlatos(neonRows, getDishOverrides());
    }
  } catch (err) {
    console.warn('fetchLiveSanitizedPlatos fallback a catálogo local:', err.message || err);
  }
  return getFallbackSanitizedPlatos();
}

function resolveDishNameById(id, fallbackName = '') {
  if (fallbackName && String(fallbackName).trim()) return String(fallbackName).trim();
  const strId = String(id || '').trim();
  if (!strId) return '';
  if (strId.startsWith('alm18-')) {
    const slug = strId.slice(6).replace(/-/g, ' ');
    const found = REQUIRED_18K_DISHES.find(
      (d) => normText(d.key).replace(/[^a-z0-9]/g, ' ') === slug || normText(d.key) === slug
    );
    if (found) return found.nombre;
  }
  if (strId.startsWith('beb-')) {
    const slug = strId.slice(4).replace(/-/g, ' ');
    const found = CALIBRATED_BEBIDAS.find(
      (b) => normText(b.key).replace(/[^a-z0-9]/g, ' ') === slug || normText(b.key) === slug
    );
    if (found) return found.nombre;
  }
  const prods = getAllProducts() || [];
  const match = prods.find((p) => String(p.id) === strId);
  if (match) return match.name || match.nombre || '';
  return '';
}

async function syncSinglePlatoDirect({ id, nombre, precio, disponible }) {
  const resolvedName = resolveDishNameById(id, nombre);

  const updatedRow = await updateSinglePlatoInNeon(
    { id, nombre: resolvedName, precio, disponible },
    3500
  );

  const finalName = updatedRow?.nombre || resolvedName || '';

  if (finalName) {
    setDishOverride(finalName, { disponible, precio });
  }
  if (id) {
    setDishOverride(String(id), { disponible, precio });
  }
  if (precio !== undefined && Number(precio) >= 0) {
    updateProductPrice(id || finalName, Number(precio), finalName);
  }
  if (disponible !== undefined) {
    toggleProductStock(id || finalName, Boolean(disponible), finalName);
  }

  return {
    id: updatedRow?.id ?? id ?? 0,
    nombre: finalName,
    precio:
      precio !== undefined
        ? Number(precio)
        : Number(updatedRow?.precio ?? 0),
    disponible:
      disponible !== undefined
        ? Boolean(disponible)
        : Boolean(updatedRow?.disponible ?? true),
    activo:
      disponible !== undefined
        ? Boolean(disponible)
        : Boolean(updatedRow?.activo ?? true),
  };
}

async function handleRequest({ params, request }) {
  const action = (params.action || '').replace(/^\/+|\/+$/g, '');
  const method = request.method.toUpperCase();

  // 1. GET /api/platos
  if (method === 'GET' && !action) {
    try {
      const list = await fetchLiveSanitizedPlatos();
      return new Response(JSON.stringify(Array.isArray(list) ? list : []), {
        status: 200,
        headers: JSON_HEADERS,
      });
    } catch (err) {
      console.error('Error en GET /api/platos fallback:', err);
      const fallbackList = getFallbackSanitizedPlatos();
      return new Response(JSON.stringify(fallbackList), {
        status: 200,
        headers: JSON_HEADERS,
      });
    }
  }

  let parsedBody = {};
  if (method !== 'GET' && method !== 'HEAD') {
    try {
      const rawBody = await request.text();
      parsedBody = rawBody ? JSON.parse(rawBody) : {};
    } catch (_) {
      parsedBody = {};
    }
  }

  // Cargar overrides actuales desde Neon DB con timeout corto (2.5s)
  await pullOverridesFromNeon(2500);

  // 2. Guardado masivo de disponibilidad y precios: POST/PUT /api/platos/bulk-save
  if (action === 'bulk-save' && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    const items = Array.isArray(parsedBody.platos)
      ? parsedBody.platos
      : Array.isArray(parsedBody.items)
      ? parsedBody.items
      : [];

    const results = [];
    for (const item of items) {
      if (!item) continue;
      const itemName = resolveDishNameById(item.id, item.nombre || item.name);
      const itemPrice = item.precio ?? item.price;
      const itemDisp = item.disponible !== undefined ? Boolean(item.disponible) : true;

      if (itemName) {
        setDishOverride(itemName, { disponible: itemDisp, precio: itemPrice });
      }
      if (item.id) {
        setDishOverride(String(item.id), { disponible: itemDisp, precio: itemPrice });
      }
      if (itemPrice !== undefined && Number(itemPrice) >= 0) {
        updateProductPrice(item.id || itemName, Number(itemPrice), itemName);
      }
      toggleProductStock(item.id || itemName, itemDisp, itemName);

      results.push({
        id: item.id,
        nombre: itemName,
        precio: Number(itemPrice || 0),
        disponible: itemDisp,
        activo: itemDisp,
      });
    }

    await pushOverridesToNeon(3500);

    return new Response(
      JSON.stringify({ ok: true, success: true, updated: results.length, platos: results }),
      {
        status: 200,
        headers: JSON_HEADERS,
      }
    );
  }

  // 3. Actualización masiva de precio de un bloque: PUT/POST /api/platos/bulk-price
  if (action === 'bulk-price' && (method === 'PUT' || method === 'POST' || method === 'PATCH')) {
    const nuevoPrecio = Number(parsedBody.nuevo_precio || 0);
    const ids = Array.isArray(parsedBody.plato_ids) ? parsedBody.plato_ids : [];
    const nombres = Array.isArray(parsedBody.nombres) ? parsedBody.nombres : [];

    const numericIds = ids.filter((x) => /^\d+$/.test(String(x))).map(Number);
    await bulkUpdatePlatosPriceInNeon({ numericIds, nombres, nuevoPrecio }, 3500);

    for (const id of ids) {
      const rName = resolveDishNameById(id);
      setDishOverride(rName || String(id), { precio: nuevoPrecio });
      updateProductPrice(id, nuevoPrecio, rName);
    }
    for (const n of nombres) {
      if (n) {
        setDishOverride(n, { precio: nuevoPrecio });
        updateProductPrice(n, nuevoPrecio, n);
      }
    }
    await pushOverridesToNeon(3500);

    return new Response(JSON.stringify({ ok: true, success: true, nuevo_precio: nuevoPrecio }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  }

  // 4. Actualización individual de disponibilidad y/o precio:
  //    Soporta /api/platos/{id}/disponibilidad, /api/platos/{id}, /api/platos/by-name y /api/platos
  if (method === 'PATCH' || method === 'PUT' || method === 'POST') {
    const dispMatch = action.match(/^([^/]+)\/disponibilidad$/i);
    const targetId = dispMatch
      ? decodeURIComponent(dispMatch[1])
      : action && action !== 'by-name' && action !== 'disponibilidad'
      ? decodeURIComponent(action)
      : parsedBody.id || '';
    const targetName = parsedBody.nombre || parsedBody.name || '';
    const targetDisp =
      parsedBody.disponible !== undefined
        ? Boolean(parsedBody.disponible)
        : parsedBody.activo !== undefined
        ? Boolean(parsedBody.activo)
        : undefined;
    const targetPrice =
      parsedBody.precio !== undefined
        ? Number(parsedBody.precio)
        : parsedBody.price !== undefined
        ? Number(parsedBody.price)
        : undefined;

    const updated = await syncSinglePlatoDirect({
      id: targetId,
      nombre: targetName,
      precio: targetPrice,
      disponible: targetDisp,
    });

    await pushOverridesToNeon(3500);

    return new Response(
      JSON.stringify({
        ok: true,
        success: true,
        ...updated,
      }),
      {
        status: 200,
        headers: JSON_HEADERS,
      }
    );
  }

  return new Response(JSON.stringify({ error: 'No se pudo procesar la solicitud de platos.' }), {
    status: 400,
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
