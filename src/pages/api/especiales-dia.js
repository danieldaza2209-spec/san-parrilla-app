import { getSanitizedFastapiUrl } from '../../lib/fastapi.js';
import { getDailySpecials, updateDailySpecials } from '../../lib/db.js';

function normalizeSpecialsPayload(raw) {
  const fallback = getDailySpecials();
  const data = raw && typeof raw === 'object' ? raw : {};

  const sopa = String(data.sopa_dia || data.sopa || fallback.sopa || 'Campesina').trim();
  const toArray = (v, def) => {
    if (Array.isArray(v) && v.length > 0) return v.map((x) => String(x).trim()).filter(Boolean);
    if (typeof v === 'string' && v.trim()) return v.split(',').map((x) => x.trim()).filter(Boolean);
    return def;
  };

  const principios = toArray(data.principios, fallback.principios || ['Calabacín al huevo', 'Lentejas caseras', 'Frijoles caseros']);
  const acompanamientos = toArray(data.acompanamientos, fallback.acompanamientos || ['Puré de ahuyama', 'Deditos', 'Tajadas maduras']);
  const especiales_16500 = toArray(data.especiales_16500, fallback.especiales_16500 || ['Hígado al ajillo', 'Desgranado de carne']);

  let rawTag165 = String(data.especiales_16500_etiqueta || fallback.especiales_16500_etiqueta || '⭐ SOLO POR HOY').trim();
  let tag165Flag = undefined;
  if (rawTag165.endsWith('||OFF')) {
    tag165Flag = false;
    rawTag165 = rawTag165.slice(0, -5).trim();
  } else if (rawTag165.endsWith('||ON')) {
    tag165Flag = true;
    rawTag165 = rawTag165.slice(0, -4).trim();
  }
  const especiales_16500_etiqueta = rawTag165 || '⭐ SOLO POR HOY';
  const mostrar_rotativos_16k =
    data.mostrar_rotativos_16k !== undefined
      ? Boolean(data.mostrar_rotativos_16k)
      : tag165Flag !== undefined
      ? tag165Flag
      : fallback.mostrar_rotativos_16k !== false;

  const especial_arroz_nombre = String(data.especial_arroz_nombre || fallback.especial_arroz_nombre || 'Arroz ranchero').trim();

  let rawTagArroz = String(data.especial_arroz_etiqueta || fallback.especial_arroz_etiqueta || '⭐ SOLO LOS LUNES').trim();
  let tagArrozFlag = undefined;
  if (rawTagArroz.endsWith('||OFF')) {
    tagArrozFlag = false;
    rawTagArroz = rawTagArroz.slice(0, -5).trim();
  } else if (rawTagArroz.endsWith('||ON')) {
    tagArrozFlag = true;
    rawTagArroz = rawTagArroz.slice(0, -4).trim();
  }
  const especial_arroz_etiqueta = rawTagArroz || '⭐ SOLO LOS LUNES';
  const mostrar_rotativo_fin_semana =
    data.mostrar_rotativo_fin_semana !== undefined
      ? Boolean(data.mostrar_rotativo_fin_semana)
      : tagArrozFlag !== undefined
      ? tagArrozFlag
      : fallback.mostrar_rotativo_fin_semana !== false;

  const especial_arroz_precio = Number(data.especial_arroz_precio || fallback.especial_arroz_precio || 18000);

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
    updated_at: data.updated_at || new Date().toISOString(),
  };
}

export async function GET() {
  const baseUrl = getSanitizedFastapiUrl();
  try {
    const res = await fetch(`${baseUrl}/api/especiales-dia`, {
      headers: { Accept: 'application/json' },
    });
    if (res.ok) {
      const remoteData = await res.json();
      const normalized = normalizeSpecialsPayload(remoteData);
      updateDailySpecials(normalized.sopa, normalized.principios, normalized.acompanamientos, normalized);
      return new Response(JSON.stringify(normalized), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, max-age=0',
        },
      });
    }
  } catch (e) {}

  const localData = normalizeSpecialsPayload(getDailySpecials());
  return new Response(JSON.stringify(localData), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}

async function handleSave(request) {
  try {
    const body = await request.json();
    const normalizedInput = normalizeSpecialsPayload(body);

    // Actualizar memoria/SQLite local inmediatamente
    updateDailySpecials(
      normalizedInput.sopa,
      normalizedInput.principios,
      normalizedInput.acompanamientos,
      normalizedInput
    );

    const baseUrl = getSanitizedFastapiUrl();
    try {
      const encodedTag165 = `${normalizedInput.especiales_16500_etiqueta}||${normalizedInput.mostrar_rotativos_16k ? 'ON' : 'OFF'}`;
      const encodedTagArroz = `${normalizedInput.especial_arroz_etiqueta}||${normalizedInput.mostrar_rotativo_fin_semana ? 'ON' : 'OFF'}`;
      const res = await fetch(`${baseUrl}/api/especiales-dia`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          sopa_dia: normalizedInput.sopa_dia,
          sopa: normalizedInput.sopa,
          principios: normalizedInput.principios,
          acompanamientos: normalizedInput.acompanamientos,
          especiales_16500: normalizedInput.especiales_16500,
          especiales_16500_etiqueta: encodedTag165,
          mostrar_rotativos_16k: normalizedInput.mostrar_rotativos_16k,
          especial_arroz_nombre: normalizedInput.especial_arroz_nombre,
          especial_arroz_etiqueta: encodedTagArroz,
          especial_arroz_precio: normalizedInput.especial_arroz_precio,
          mostrar_rotativo_fin_semana: normalizedInput.mostrar_rotativo_fin_semana,
        }),
      });
      if (res.ok) {
        const savedRemote = await res.json();
        const finalData = normalizeSpecialsPayload({
          ...savedRemote,
          mostrar_rotativos_16k: normalizedInput.mostrar_rotativos_16k,
          mostrar_rotativo_fin_semana: normalizedInput.mostrar_rotativo_fin_semana,
        });
        updateDailySpecials(finalData.sopa, finalData.principios, finalData.acompanamientos, finalData);
        return new Response(JSON.stringify({ success: true, ...finalData, specials: finalData }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    } catch (e) {}

    return new Response(JSON.stringify({ success: true, ...normalizedInput, specials: normalizedInput }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function PUT({ request }) {
  return handleSave(request);
}

export async function POST({ request }) {
  return handleSave(request);
}
