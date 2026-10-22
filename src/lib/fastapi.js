const FASTAPI_URL =
  process.env.PUBLIC_API_URL ||
  process.env.FASTAPI_URL ||
  (typeof import.meta !== 'undefined' && import.meta.env
    ? (import.meta.env.PUBLIC_API_URL || import.meta.env.FASTAPI_URL)
    : null) ||
  'http://127.0.0.1:8000';

export async function proxyToFastAPI(request, targetPath) {
  const url = new URL(request.url);
  const targetUrl = new URL(targetPath, FASTAPI_URL);
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
    const response = await fetch(targetUrl.toString(), options);
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
        error: `Error comunicando con el backend FastAPI en ${FASTAPI_URL}: ${err.message}`,
      }),
      {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

export { FASTAPI_URL };
