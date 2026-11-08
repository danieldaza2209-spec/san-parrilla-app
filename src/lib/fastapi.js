const DEFAULT_RENDER_URL = 'https://san-parrilla-backend.onrender.com';

export function getSanitizedFastapiUrl() {
  let raw =
    process.env.PUBLIC_API_URL ||
    process.env.FASTAPI_URL ||
    (typeof import.meta !== 'undefined' && import.meta.env
      ? (import.meta.env.PUBLIC_API_URL || import.meta.env.FASTAPI_URL)
      : null);

  raw = String(raw || '').trim();

  if (!raw || raw === 'undefined' || raw === 'null') {
    return DEFAULT_RENDER_URL;
  }

  if (raw.startsWith('ttps://')) {
    raw = 'h' + raw;
  } else if (raw.startsWith('tp://')) {
    raw = 'ht' + raw;
  }

  if (!raw.startsWith('http://') && !raw.startsWith('https://')) {
    raw = `https://${raw}`;
  }

  return raw.replace(/\/+$/, '');
}

const FASTAPI_URL = getSanitizedFastapiUrl();

async function fetchWithRetry(url, options = {}, maxRetries = 0) {
  const { timeoutMs = 5500, ...fetchOpts } = options;
  let lastError = null;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
      const res = await fetch(url, { ...fetchOpts, signal: controller.signal });
      clearTimeout(timeoutId);

      if ([502, 503, 504].includes(res.status) && attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 600));
        continue;
      }
      return res;
    } catch (err) {
      lastError = err;
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 600));
      }
    }
  }
  throw lastError;
}

export async function proxyToFastAPI(request, targetPath) {
  const baseUrl = getSanitizedFastapiUrl();
  const url = new URL(request.url);
  const cleanPath = targetPath.startsWith('/') ? targetPath : `/${targetPath}`;
  const targetUrl = new URL(cleanPath, baseUrl);
  targetUrl.search = url.search;

  const headers = new Headers();
  for (const [key, value] of request.headers.entries()) {
    if (['content-type', 'authorization', 'accept'].includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  }

  const options = {
    method: request.method,
    headers,
    timeoutMs: 5500,
  };

  if (!['GET', 'HEAD'].includes(request.method.toUpperCase())) {
    try {
      const bodyText = await request.text();
      if (bodyText) {
        options.body = bodyText;
      }
    } catch (e) {}
  }

  try {
    const response = await fetchWithRetry(targetUrl.toString(), options, 0);
    const data = await response.text();
    return new Response(data, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('content-type') || 'application/json',
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: `Error comunicando con el backend FastAPI en ${baseUrl}: ${err.message}`,
      }),
      {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

export async function fetchFastapi(targetPath, options = {}) {
  const baseUrl = getSanitizedFastapiUrl();
  const cleanPath = targetPath.startsWith('/') ? targetPath : `/${targetPath}`;
  const targetUrl = new URL(cleanPath, baseUrl);
  return fetchWithRetry(targetUrl.toString(), options, 0);
}

export { FASTAPI_URL };
