import { getSanitizedFastapiUrl } from '../../lib/fastapi.js';
import { getDailySpecials } from '../../lib/db.js';
import {
  getLiveSpecialsFromNeon,
  upsertDailySpecialsToNeon,
} from '../../lib/neon.js';

export const prerender = false;

const JSON_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store, max-age=0',
};

export async function GET() {
  try {
    const neonSpecials = await getLiveSpecialsFromNeon(3500);
    if (neonSpecials && (neonSpecials.sopa || neonSpecials.sopa_dia)) {
      return new Response(JSON.stringify(neonSpecials), {
        status: 200,
        headers: JSON_HEADERS,
      });
    }
  } catch (err) {
    console.warn('Error en GET /api/especiales-dia Neon:', err);
  }

  const fallback = getDailySpecials();
  return new Response(JSON.stringify(fallback), {
    status: 200,
    headers: JSON_HEADERS,
  });
}

async function handleSave(request) {
  try {
    let body = {};
    try {
      body = await request.json();
    } catch (_) {
      body = {};
    }

    // 1. Guardar directamente en Neon DB y memoria local con timeout máximo de 5s
    const saved = await upsertDailySpecialsToNeon(body, 5000);

    // 2. Notificación en segundo plano a FastAPI (fire-and-forget, NUNCA bloquea ni arroja 502/504)
    try {
      const baseUrl = getSanitizedFastapiUrl();
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      fetch(`${baseUrl}/api/especiales-dia`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          sopa_dia: saved.sopa_dia,
          sopa: saved.sopa,
          principios: saved.principios,
          acompanamientos: saved.acompanamientos,
          especiales_16500: saved.especiales_16500,
          especiales_16500_etiqueta: `${saved.especiales_16500_etiqueta}||${saved.mostrar_rotativos_16k ? 'ON' : 'OFF'}`,
          especial_arroz_nombre: saved.especial_arroz_nombre,
          especial_arroz_etiqueta: `${saved.especial_arroz_etiqueta}||${saved.mostrar_rotativo_fin_semana ? 'ON' : 'OFF'}`,
          especial_arroz_precio: saved.especial_arroz_precio,
        }),
        signal: controller.signal,
      })
        .then(() => clearTimeout(timeoutId))
        .catch(() => clearTimeout(timeoutId));
    } catch (_) {}

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Especiales guardados con éxito en Neon DB',
        ...saved,
        specials: saved,
      }),
      {
        status: 200,
        headers: JSON_HEADERS,
      }
    );
  } catch (err) {
    console.error('Error en POST/PUT /api/especiales-dia:', err);
    return new Response(
      JSON.stringify({
        error: err.message || 'Error guardando especiales del día',
      }),
      {
        status: 500,
        headers: JSON_HEADERS,
      }
    );
  }
}

export async function PUT({ request }) {
  return handleSave(request);
}

export async function POST({ request }) {
  return handleSave(request);
}
