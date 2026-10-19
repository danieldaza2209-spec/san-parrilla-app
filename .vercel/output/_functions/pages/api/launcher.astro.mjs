export { renderers } from '../../renderers.mjs';

/**
 * Genera el lanzador "San Parrilla POS.bat" para el PC de caja (Windows).
 * Ruta protegida: solo Administrador (ver src/lib/auth.js).
 *
 * Detalles que importan:
 *  - --kiosk-printing imprime directo a la impresora PREDETERMINADA, sin diálogo.
 *  - Chrome ignora flags de línea de comandos si ya hay una instancia abierta con el mismo perfil,
 *    por eso se usa --user-data-dir propio: así el flag siempre se aplica y la sesión del POS
 *    queda separada del Chrome personal de quien use el PC.
 *  - Si no hay Chrome, se intenta con Edge (acepta los mismos flags).
 */
async function GET({ request }) {
  const origin = new URL(request.url).origin;

  const lines = [
    '@echo off',
    'rem ==========================================================',
    'rem  San Parrilla POS - Lanzador para el PC de caja',
    'rem  Imprime directo a la impresora PREDETERMINADA de Windows',
    'rem  (deja la SAT Q22 como predeterminada).',
    'rem ==========================================================',
    `set "URL=${origin}/pos"`,
    'set "PERFIL=%LOCALAPPDATA%\\SanParrillaPOS"',
    '',
    'set "NAVEGADOR="',
    'if exist "%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe" set "NAVEGADOR=%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"',
    'if not defined NAVEGADOR if exist "%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe" set "NAVEGADOR=%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"',
    'if not defined NAVEGADOR if exist "%LocalAppData%\\Google\\Chrome\\Application\\chrome.exe" set "NAVEGADOR=%LocalAppData%\\Google\\Chrome\\Application\\chrome.exe"',
    'if not defined NAVEGADOR if exist "%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe" set "NAVEGADOR=%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe"',
    'if not defined NAVEGADOR if exist "%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe" set "NAVEGADOR=%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe"',
    '',
    'if not defined NAVEGADOR (',
    '  echo No se encontro Google Chrome ni Microsoft Edge en este equipo.',
    '  pause',
    '  exit /b 1',
    ')',
    '',
    'start "" "%NAVEGADOR%" --app="%URL%" --kiosk-printing --user-data-dir="%PERFIL%" --no-first-run --no-default-browser-check',
    'exit /b 0',
    '',
  ];

  // Windows espera saltos de línea CRLF en archivos .bat
  const body = lines.join('\r\n');

  return new Response(body, {
    status: 200,
    headers: {
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': 'attachment; filename="San Parrilla POS.bat"',
      'Cache-Control': 'no-store',
    },
  });
}

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  GET
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
