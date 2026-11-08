import { neon } from '@neondatabase/serverless';
import {
  extractOverridesFromAcomp,
  getDailySpecials,
  updateDailySpecials,
  getDishOverrides,
  resolveCanonicalDish,
  normalizeCanonicalDishName,
} from './db.js';

const DEFAULT_DATABASE_URL =
  'postgresql://neondb_owner:npg_YrimJ8OF3SKX@ep-restless-sky-b5pjlnix-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require';

export function getDatabaseUrl() {
  return (
    process.env.DATABASE_URL ||
    process.env.NEON_DATABASE_URL ||
    process.env.POSTGRES_URL ||
    DEFAULT_DATABASE_URL
  );
}

let sqlInstance = null;

export function getNeonSql() {
  if (!sqlInstance) {
    const url = getDatabaseUrl();
    sqlInstance = neon(url);
  }
  return sqlInstance;
}

export async function queryNeonWithTimeout(queryPromise, timeoutMs = 3500) {
  let timeoutId;
  const timeoutPromise = new Promise((_, reject) => {
    timeoutId = setTimeout(
      () => reject(new Error(`Neon DB timeout (${timeoutMs}ms)`)),
      timeoutMs
    );
  });
  try {
    const res = await Promise.race([queryPromise, timeoutPromise]);
    clearTimeout(timeoutId);
    return res;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}

export function parseDailySpecialsRow(row) {
  if (!row) return null;
  const fallback = getDailySpecials();

  const toList = (raw, def) => {
    if (Array.isArray(raw)) return raw.map(String).map((s) => s.trim()).filter(Boolean);
    if (typeof raw === 'string' && raw.trim()) {
      return raw.split(',').map((s) => s.trim()).filter(Boolean);
    }
    return def;
  };

  const sopa = String(row.sopa_dia || row.sopa || fallback.sopa || 'Campesina').trim();
  const principios = toList(row.principios, fallback.principios || []);
  const rawAcomp = toList(row.acompanamientos, fallback.acompanamientos || []);
  const { cleanAcomp } = extractOverridesFromAcomp(rawAcomp);
  const acompanamientos = cleanAcomp.length > 0 ? cleanAcomp : (fallback.acompanamientos || []);
  const especiales_16500 = toList(row.especiales_16500, fallback.especiales_16500 || []);

  let rawTag165 = String(row.especiales_16500_etiqueta || fallback.especiales_16500_etiqueta || '⭐ SOLO POR HOY').trim();
  let tag165Flag = undefined;
  if (rawTag165.endsWith('||OFF')) {
    tag165Flag = false;
    rawTag165 = rawTag165.slice(0, -5).trim();
  } else if (rawTag165.endsWith('||ON')) {
    tag165Flag = true;
    rawTag165 = rawTag165.slice(0, -4).trim();
  }
  const especiales_16500_etiqueta = rawTag165 || '⭐ SOLO POR HOY';
  const mostrar_rotativos_16k = tag165Flag !== undefined ? tag165Flag : (fallback.mostrar_rotativos_16k !== false);

  const especial_arroz_nombre = String(row.especial_arroz_nombre || fallback.especial_arroz_nombre || 'Arroz ranchero').trim();

  let rawTagArroz = String(row.especial_arroz_etiqueta || fallback.especial_arroz_etiqueta || '⭐ FIN DE SEMANA').trim();
  let tagArrozFlag = undefined;
  if (rawTagArroz.endsWith('||OFF')) {
    tagArrozFlag = false;
    rawTagArroz = rawTagArroz.slice(0, -5).trim();
  } else if (rawTagArroz.endsWith('||ON')) {
    tagArrozFlag = true;
    rawTagArroz = rawTagArroz.slice(0, -4).trim();
  }
  const especial_arroz_etiqueta = rawTagArroz || '⭐ FIN DE SEMANA';
  const mostrar_rotativo_fin_semana = tagArrozFlag !== undefined ? tagArrozFlag : (fallback.mostrar_rotativo_fin_semana !== false);

  const especial_arroz_precio = Number(row.especial_arroz_precio || fallback.especial_arroz_precio || 18000);

  return {
    sopa_dia: sopa,
    sopa,
    principios,
    principios_str: principios.join(', '),
    acompanamientos,
    acompanamientos_str: acompanamientos.join(', '),
    especiales_16500,
    especiales_16500_str: especiales_16500.join(', '),
    especiales_16500_etiqueta,
    mostrar_rotativos_16k,
    especial_arroz_nombre,
    especial_arroz_etiqueta,
    especial_arroz_precio,
    mostrar_rotativo_fin_semana,
    updated_at: row.updated_at || new Date().toISOString(),
  };
}

export async function getLiveSpecialsFromNeon(timeoutMs = 3000) {
  try {
    const sql = getNeonSql();
    const rows = await queryNeonWithTimeout(
      sql`SELECT * FROM daily_specials_config WHERE id = 1 LIMIT 1`,
      timeoutMs
    );
    if (Array.isArray(rows) && rows.length > 0) {
      const parsed = parseDailySpecialsRow(rows[0]);
      if (parsed) {
        updateDailySpecials(parsed.sopa, parsed.principios, parsed.acompanamientos, parsed);
        return parsed;
      }
    }
  } catch (err) {
    console.warn('getLiveSpecialsFromNeon fallback:', err.message || err);
  }
  return null;
}

export async function upsertDailySpecialsToNeon(data, timeoutMs = 4500) {
  const fallback = getDailySpecials();
  const input = data && typeof data === 'object' ? data : {};

  const sopa = String(input.sopa_dia || input.sopa || fallback.sopa || 'Campesina').trim();
  const toList = (v, def) => {
    if (Array.isArray(v)) return v.map(String).map((s) => s.trim()).filter(Boolean);
    if (typeof v === 'string' && v.trim()) return v.split(',').map((s) => s.trim()).filter(Boolean);
    return def;
  };

  const principios = toList(input.principios, fallback.principios || []);
  const rawAcomp = toList(input.acompanamientos, fallback.acompanamientos || []);
  const { cleanAcomp } = extractOverridesFromAcomp(rawAcomp);
  const acompanamientos = cleanAcomp.length > 0 ? cleanAcomp : (fallback.acompanamientos || []);
  const especiales_16500 = toList(input.especiales_16500, fallback.especiales_16500 || []);

  const cleanTag165 = String(input.especiales_16500_etiqueta || fallback.especiales_16500_etiqueta || '⭐ SOLO POR HOY')
    .replace(/\|\|(ON|OFF)$/i, '')
    .trim();
  const mostrar_16k =
    input.mostrar_rotativos_16k !== undefined
      ? Boolean(input.mostrar_rotativos_16k)
      : fallback.mostrar_rotativos_16k !== false;
  const encodedTag165 = `${cleanTag165}||${mostrar_16k ? 'ON' : 'OFF'}`;

  const especial_arroz_nombre = String(input.especial_arroz_nombre || fallback.especial_arroz_nombre || 'Arroz ranchero').trim();
  const cleanTagArroz = String(input.especial_arroz_etiqueta || fallback.especial_arroz_etiqueta || '⭐ FIN DE SEMANA')
    .replace(/\|\|(ON|OFF)$/i, '')
    .trim();
  const mostrar_fin_semana =
    input.mostrar_rotativo_fin_semana !== undefined
      ? Boolean(input.mostrar_rotativo_fin_semana)
      : fallback.mostrar_rotativo_fin_semana !== false;
  const encodedTagArroz = `${cleanTagArroz}||${mostrar_fin_semana ? 'ON' : 'OFF'}`;

  const especial_arroz_precio = Number(input.especial_arroz_precio || fallback.especial_arroz_precio || 18000);

  const principios_str = principios.join(', ');
  const acomp_str = acompanamientos.join(', ');
  const esp165_str = especiales_16500.join(', ');

  const normalized = {
    sopa_dia: sopa,
    sopa,
    principios,
    principios_str,
    acompanamientos,
    acompanamientos_str: acompanamientos.join(', '),
    especiales_16500,
    especiales_16500_str: esp165_str,
    especiales_16500_etiqueta: cleanTag165,
    mostrar_rotativos_16k: mostrar_16k,
    especial_arroz_nombre,
    especial_arroz_etiqueta: cleanTagArroz,
    especial_arroz_precio,
    mostrar_rotativo_fin_semana: mostrar_fin_semana,
    updated_at: new Date().toISOString(),
  };

  updateDailySpecials(sopa, principios, acompanamientos, normalized);

  const sql = getNeonSql();
  try {
    const rows = await queryNeonWithTimeout(
      sql`
        INSERT INTO daily_specials_config (
          id, sopa_dia, principios, acompanamientos, especiales_16500, especiales_16500_etiqueta,
          especial_arroz_nombre, especial_arroz_etiqueta, especial_arroz_precio, updated_at
        ) VALUES (
          1, ${sopa}, ${principios_str}, ${acomp_str}, ${esp165_str}, ${encodedTag165},
          ${especial_arroz_nombre}, ${encodedTagArroz}, ${especial_arroz_precio}, NOW()
        )
        ON CONFLICT (id) DO UPDATE SET
          sopa_dia = EXCLUDED.sopa_dia,
          principios = EXCLUDED.principios,
          acompanamientos = EXCLUDED.acompanamientos,
          especiales_16500 = EXCLUDED.especiales_16500,
          especiales_16500_etiqueta = EXCLUDED.especiales_16500_etiqueta,
          especial_arroz_nombre = EXCLUDED.especial_arroz_nombre,
          especial_arroz_etiqueta = EXCLUDED.especial_arroz_etiqueta,
          especial_arroz_precio = EXCLUDED.especial_arroz_precio,
          updated_at = NOW()
        RETURNING *;
      `,
      timeoutMs
    );
    if (Array.isArray(rows) && rows.length > 0) {
      const parsedRow = parseDailySpecialsRow(rows[0]);
      if (parsedRow) return parsedRow;
    }
  } catch (err) {
    console.error('upsertDailySpecialsToNeon error:', err.message || err);
  }

  return normalized;
}

export async function pullOverridesFromNeon() {
  return getDishOverrides();
}

export async function pushOverridesToNeon() {
  return true;
}

export async function fetchPlatosFromNeon(timeoutMs = 3500) {
  const sql = getNeonSql();
  const platosRows = await queryNeonWithTimeout(
    sql`
      SELECT id, categoria_id, nombre, descripcion, precio, imagen_emoji, activo, disponible
      FROM platos
      ORDER BY categoria_id ASC, precio ASC, id ASC
    `,
    timeoutMs
  );

  return Array.isArray(platosRows) ? platosRows : [];
}

export async function updateSinglePlatoInNeon({ id, nombre, precio, disponible }, timeoutMs = 3500) {
  const sql = getNeonSql();
  const canonical = resolveCanonicalDish(id, nombre);
  const isNumId = /^\d+$/.test(String(id || '').trim());
  const numId = isNumId ? Number(id) : null;
  const targetNumIds = canonical
    ? Array.from(new Set([...canonical.neonIds, ...(numId !== null ? [numId] : [])]))
    : numId !== null
    ? [numId]
    : [];
  const cleanName = canonical ? canonical.nombre : normalizeCanonicalDishName(nombre || '');
  const hasPrice = precio !== undefined && Number(precio) >= 0;
  const hasDisp = disponible !== undefined;
  const dispVal = hasDisp ? Boolean(disponible) : true;
  const priceVal = hasPrice ? Number(precio) : 0;

  let updatedRow = null;

  try {
    if (targetNumIds.length > 0) {
      if (hasDisp && hasPrice) {
        const rows = await queryNeonWithTimeout(
          sql`
            UPDATE platos
            SET disponible = ${dispVal}, activo = ${dispVal}, precio = ${priceVal}
            WHERE id = ANY(${targetNumIds})
            RETURNING id, categoria_id, nombre, descripcion, precio, activo, disponible
          `,
          timeoutMs
        );
        if (rows?.length > 0) updatedRow = rows[0];
      } else if (hasDisp) {
        const rows = await queryNeonWithTimeout(
          sql`
            UPDATE platos
            SET disponible = ${dispVal}, activo = ${dispVal}
            WHERE id = ANY(${targetNumIds})
            RETURNING id, categoria_id, nombre, descripcion, precio, activo, disponible
          `,
          timeoutMs
        );
        if (rows?.length > 0) updatedRow = rows[0];
      } else if (hasPrice) {
        const rows = await queryNeonWithTimeout(
          sql`
            UPDATE platos
            SET precio = ${priceVal}
            WHERE id = ANY(${targetNumIds})
            RETURNING id, categoria_id, nombre, descripcion, precio, activo, disponible
          `,
          timeoutMs
        );
        if (rows?.length > 0) updatedRow = rows[0];
      }
    }

    const nameToMatch = cleanName || updatedRow?.nombre || '';
    if (nameToMatch) {
      const lower = nameToMatch.toLowerCase();
      const variants = canonical
        ? Array.from(new Set([canonical.nombre.toLowerCase(), ...canonical.aliases]))
        : lower === 'espagueti con pollo' || lower === 'espaguetis con pollo'
        ? ['espagueti con pollo', 'espaguetis con pollo']
        : lower === 'picada x 1' || lower === 'picada por uno' || lower === 'picada por 1'
        ? ['picada x 1', 'picada por uno', 'picada por 1']
        : [lower];

      if (hasDisp && hasPrice) {
        const rows = await queryNeonWithTimeout(
          sql`
            UPDATE platos
            SET disponible = ${dispVal}, activo = ${dispVal}, precio = ${priceVal}
            WHERE LOWER(TRIM(nombre)) = ANY(${variants})
            RETURNING id, categoria_id, nombre, descripcion, precio, activo, disponible
          `,
          timeoutMs
        );
        if (!updatedRow && rows?.length > 0) updatedRow = rows[0];
      } else if (hasDisp) {
        const rows = await queryNeonWithTimeout(
          sql`
            UPDATE platos
            SET disponible = ${dispVal}, activo = ${dispVal}
            WHERE LOWER(TRIM(nombre)) = ANY(${variants})
            RETURNING id, categoria_id, nombre, descripcion, precio, activo, disponible
          `,
          timeoutMs
        );
        if (!updatedRow && rows?.length > 0) updatedRow = rows[0];
      } else if (hasPrice) {
        const rows = await queryNeonWithTimeout(
          sql`
            UPDATE platos
            SET precio = ${priceVal}
            WHERE LOWER(TRIM(nombre)) = ANY(${variants})
            RETURNING id, categoria_id, nombre, descripcion, precio, activo, disponible
          `,
          timeoutMs
        );
        if (!updatedRow && rows?.length > 0) updatedRow = rows[0];
      }
    }
  } catch (err) {
    console.warn('updateSinglePlatoInNeon warning:', err.message || err);
  }

  return updatedRow;
}

export async function bulkSavePlatosInNeon(items = [], timeoutMs = 4500) {
  if (!Array.isArray(items) || items.length === 0) return [];
  const results = await Promise.all(
    items.map((item) =>
      updateSinglePlatoInNeon(
        {
          id: item.id,
          nombre: item.nombre || item.name,
          precio: item.precio ?? item.price,
          disponible: item.disponible !== undefined ? Boolean(item.disponible) : Boolean(item.activo ?? true),
        },
        timeoutMs
      ).catch(() => null)
    )
  );
  return results.filter(Boolean);
}

export async function bulkUpdatePlatosPriceInNeon({ numericIds = [], nombres = [], nuevoPrecio }, timeoutMs = 4000) {
  const sql = getNeonSql();
  const priceVal = Number(nuevoPrecio || 0);
  const cleanNames = nombres.map((n) => String(n || '').trim().toLowerCase()).filter(Boolean);

  try {
    if (numericIds.length > 0 && cleanNames.length > 0) {
      await queryNeonWithTimeout(
        sql`
          UPDATE platos
          SET precio = ${priceVal}
          WHERE id = ANY(${numericIds}) OR LOWER(TRIM(nombre)) = ANY(${cleanNames})
        `,
        timeoutMs
      );
    } else if (numericIds.length > 0) {
      await queryNeonWithTimeout(
        sql`
          UPDATE platos
          SET precio = ${priceVal}
          WHERE id = ANY(${numericIds})
        `,
        timeoutMs
      );
    } else if (cleanNames.length > 0) {
      await queryNeonWithTimeout(
        sql`
          UPDATE platos
          SET precio = ${priceVal}
          WHERE LOWER(TRIM(nombre)) = ANY(${cleanNames})
        `,
        timeoutMs
      );
    }
    return true;
  } catch (err) {
    console.warn('bulkUpdatePlatosPriceInNeon warning:', err.message || err);
    return false;
  }
}

export async function fetchPedidosFromNeon({ limit = 500, estado = null } = {}, timeoutMs = 4500) {
  const sql = getNeonSql();
  const safeLimit = Math.min(Math.max(Number(limit) || 200, 1), 600);

  const orders = estado
    ? await queryNeonWithTimeout(
        sql`SELECT * FROM pedidos WHERE estado = ${estado} ORDER BY id DESC LIMIT ${safeLimit}`,
        timeoutMs
      )
    : await queryNeonWithTimeout(
        sql`SELECT * FROM pedidos ORDER BY id DESC LIMIT ${safeLimit}`,
        timeoutMs
      );

  if (!Array.isArray(orders) || orders.length === 0) return [];

  const orderIds = orders.map((o) => Number(o.id)).filter(Boolean);

  const [detalles, payments] = await queryNeonWithTimeout(
    Promise.all([
      sql`
        SELECT d.*, p.nombre AS plato_nombre, p.precio AS plato_precio, p.categoria_id AS plato_categoria_id
        FROM detalles_pedido d
        LEFT JOIN platos p ON p.id = d.plato_id
        WHERE d.pedido_id = ANY(${orderIds})
        ORDER BY d.id ASC
      `.catch(() => []),
      sql`
        SELECT * FROM payments
        WHERE pedido_id = ANY(${orderIds})
        ORDER BY id ASC
      `.catch(() => []),
    ]),
    timeoutMs
  );

  const detallesByOrder = new Map();
  for (const d of detalles || []) {
    const pid = Number(d.pedido_id);
    if (!detallesByOrder.has(pid)) detallesByOrder.set(pid, []);
    detallesByOrder.get(pid).push({
      id: d.id,
      pedido_id: pid,
      plato_id: d.plato_id,
      cantidad: Number(d.cantidad || 1),
      precio_unitario: Number(d.precio_unitario ?? d.plato_precio ?? 0),
      notas_item: d.notas_item || '',
      impreso_cocina: Boolean(d.impreso_cocina),
      comensal_nombre: d.comensal_nombre || null,
      nombre_plato: d.plato_nombre || 'Plato',
      plato: {
        id: d.plato_id,
        nombre: d.plato_nombre || 'Plato',
        precio: Number(d.plato_precio ?? d.precio_unitario ?? 0),
        categoria_id: d.plato_categoria_id || 1,
      },
    });
  }

  const paymentsByOrder = new Map();
  for (const pay of payments || []) {
    const pid = Number(pay.pedido_id);
    if (!paymentsByOrder.has(pid)) paymentsByOrder.set(pid, []);
    paymentsByOrder.get(pid).push({
      id: pay.id,
      pedido_id: pid,
      cash_closure_id: pay.cash_closure_id,
      method: pay.method,
      amount: Number(pay.amount || 0),
      change_given: Number(pay.change_given || 0),
      created_at: pay.created_at,
    });
  }

  return orders.map((o) => {
    const pid = Number(o.id);
    return {
      ...o,
      subtotal: Number(o.subtotal || 0),
      delivery_fee: Number(o.delivery_fee || 0),
      packaging_fee: Number(o.packaging_fee || 0),
      total: Number(o.total || 0),
      detalles: detallesByOrder.get(pid) || [],
      payments: paymentsByOrder.get(pid) || [],
    };
  });
}

export async function fetchActiveCajaFromNeon(timeoutMs = 3500) {
  const sql = getNeonSql();
  const rows = await queryNeonWithTimeout(
    sql`SELECT * FROM cash_closures WHERE status = 'OPEN' ORDER BY id DESC LIMIT 1`,
    timeoutMs
  );
  if (Array.isArray(rows) && rows.length > 0) {
    return rows[0];
  }
  return null;
}

export async function fetchClientesFromNeon({ q = '', phone = '' } = {}, timeoutMs = 3500) {
  const sql = getNeonSql();
  if (phone && phone.trim()) {
    const rows = await queryNeonWithTimeout(
      sql`SELECT * FROM clientes WHERE telefono = ${phone.trim()} ORDER BY id DESC LIMIT 10`,
      timeoutMs
    );
    return Array.isArray(rows) ? rows : [];
  }
  if (q && q.trim()) {
    const pattern = `%${q.trim()}%`;
    const rows = await queryNeonWithTimeout(
      sql`
        SELECT * FROM clientes
        WHERE nombre ILIKE ${pattern} OR telefono ILIKE ${pattern} OR direccion ILIKE ${pattern}
        ORDER BY nombre ASC
        LIMIT 100
      `,
      timeoutMs
    );
    return Array.isArray(rows) ? rows : [];
  }
  const rows = await queryNeonWithTimeout(
    sql`SELECT * FROM clientes ORDER BY nombre ASC LIMIT 500`,
    timeoutMs
  );
  return Array.isArray(rows) ? rows : [];
}

export async function fetchMensajerosFromNeon({ incluirInactivos = true } = {}, timeoutMs = 3500) {
  const sql = getNeonSql();
  const rows = incluirInactivos
    ? await queryNeonWithTimeout(sql`SELECT * FROM mensajeros ORDER BY id ASC`, timeoutMs)
    : await queryNeonWithTimeout(sql`SELECT * FROM mensajeros WHERE activo = true ORDER BY id ASC`, timeoutMs);
  return Array.isArray(rows) ? rows : [];
}
