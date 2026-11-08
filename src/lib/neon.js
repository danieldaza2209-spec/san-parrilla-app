import { neon } from '@neondatabase/serverless';
import {
  extractOverridesFromAcomp,
  encodeOverridesToken,
  getDailySpecials,
  updateDailySpecials,
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
    let timeoutId;
    const timeoutPromise = new Promise((_, reject) => {
      timeoutId = setTimeout(() => reject(new Error('Neon query timeout')), timeoutMs);
    });
    const queryPromise = sql`SELECT * FROM daily_specials_config WHERE id = 1 LIMIT 1`;
    const rows = await Promise.race([queryPromise, timeoutPromise]);
    clearTimeout(timeoutId);
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

export async function upsertDailySpecialsToNeon(data, timeoutMs = 5000) {
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

  // Re-encode overrides token into acompanamientos string to preserve catalog availability overrides
  const ovrToken = encodeOverridesToken();
  const finalAcompList = ovrToken ? [...acompanamientos, ovrToken] : acompanamientos;

  const principios_str = principios.join(', ');
  const acomp_str = finalAcompList.join(', ');
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

  // Actualizar memoria local de inmediato
  updateDailySpecials(sopa, principios, acompanamientos, normalized);

  const sql = getNeonSql();
  let timeoutId;
  const timeoutPromise = new Promise((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error('Neon upsert query timeout')), timeoutMs);
  });

  const queryPromise = sql`
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
  `;

  try {
    const rows = await Promise.race([queryPromise, timeoutPromise]);
    clearTimeout(timeoutId);
    if (Array.isArray(rows) && rows.length > 0) {
      const parsedRow = parseDailySpecialsRow(rows[0]);
      if (parsedRow) return parsedRow;
    }
  } catch (err) {
    clearTimeout(timeoutId);
    console.error('upsertDailySpecialsToNeon error, returning local normalized state:', err.message || err);
  }

  return normalized;
}
