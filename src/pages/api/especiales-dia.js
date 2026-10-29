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
  const especiales_16500_etiqueta = String(data.especiales_16500_etiqueta || fallback.especiales_16500_etiqueta || '⭐ SOLO POR HOY').trim();
  const especial_arroz_nombre = String(data.especial_arroz_nombre || fallback.especial_arroz_nombre || 'Arroz ranchero').trim();
  const especial_arroz_etiqueta = String(data.especial_arroz_etiqueta || fallback.especial_arroz_etiqueta || '⭐ SOLO LOS LUNES').trim();
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
    especial_arroz_nombre,
    especial_arroz_etiqueta,
    especial_arroz_precio,
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
          especiales_16500_etiqueta: normalizedInput.especiales_16500_etiqueta,
          especial_arroz_nombre: normalizedInput.especial_arroz_nombre,
          especial_arroz_etiqueta: normalizedInput.especial_arroz_etiqueta,
          especial_arroz_precio: normalizedInput.especial_arroz_precio,
        }),
      });
      if (res.ok) {
        const savedRemote = await res.json();
        const finalData = normalizeSpecialsPayload(savedRemote);
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
