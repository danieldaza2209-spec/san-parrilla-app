import 'piccolore';
import { q as decodeKey } from './chunks/astro/server_CKkv12kC.mjs';
import 'clsx';
import { N as NOOP_MIDDLEWARE_FN } from './chunks/astro-designed-error-pages_Bfd0zdKk.mjs';
import 'es-module-lexer';

function sanitizeParams(params) {
  return Object.fromEntries(
    Object.entries(params).map(([key, value]) => {
      if (typeof value === "string") {
        return [key, value.normalize().replace(/#/g, "%23").replace(/\?/g, "%3F")];
      }
      return [key, value];
    })
  );
}
function getParameter(part, params) {
  if (part.spread) {
    return params[part.content.slice(3)] || "";
  }
  if (part.dynamic) {
    if (!params[part.content]) {
      throw new TypeError(`Missing parameter: ${part.content}`);
    }
    return params[part.content];
  }
  return part.content.normalize().replace(/\?/g, "%3F").replace(/#/g, "%23").replace(/%5B/g, "[").replace(/%5D/g, "]");
}
function getSegment(segment, params) {
  const segmentPath = segment.map((part) => getParameter(part, params)).join("");
  return segmentPath ? "/" + segmentPath : "";
}
function getRouteGenerator(segments, addTrailingSlash) {
  return (params) => {
    const sanitizedParams = sanitizeParams(params);
    let trailing = "";
    if (addTrailingSlash === "always" && segments.length) {
      trailing = "/";
    }
    const path = segments.map((segment) => getSegment(segment, sanitizedParams)).join("") + trailing;
    return path || "/";
  };
}

function deserializeRouteData(rawRouteData) {
  return {
    route: rawRouteData.route,
    type: rawRouteData.type,
    pattern: new RegExp(rawRouteData.pattern),
    params: rawRouteData.params,
    component: rawRouteData.component,
    generate: getRouteGenerator(rawRouteData.segments, rawRouteData._meta.trailingSlash),
    pathname: rawRouteData.pathname || void 0,
    segments: rawRouteData.segments,
    prerender: rawRouteData.prerender,
    redirect: rawRouteData.redirect,
    redirectRoute: rawRouteData.redirectRoute ? deserializeRouteData(rawRouteData.redirectRoute) : void 0,
    fallbackRoutes: rawRouteData.fallbackRoutes.map((fallback) => {
      return deserializeRouteData(fallback);
    }),
    isIndex: rawRouteData.isIndex,
    origin: rawRouteData.origin
  };
}

function deserializeManifest(serializedManifest) {
  const routes = [];
  for (const serializedRoute of serializedManifest.routes) {
    routes.push({
      ...serializedRoute,
      routeData: deserializeRouteData(serializedRoute.routeData)
    });
    const route = serializedRoute;
    route.routeData = deserializeRouteData(serializedRoute.routeData);
  }
  const assets = new Set(serializedManifest.assets);
  const componentMetadata = new Map(serializedManifest.componentMetadata);
  const inlinedScripts = new Map(serializedManifest.inlinedScripts);
  const clientDirectives = new Map(serializedManifest.clientDirectives);
  const serverIslandNameMap = new Map(serializedManifest.serverIslandNameMap);
  const key = decodeKey(serializedManifest.key);
  return {
    // in case user middleware exists, this no-op middleware will be reassigned (see plugin-ssr.ts)
    middleware() {
      return { onRequest: NOOP_MIDDLEWARE_FN };
    },
    ...serializedManifest,
    assets,
    componentMetadata,
    inlinedScripts,
    clientDirectives,
    routes,
    serverIslandNameMap,
    key
  };
}

const manifest = deserializeManifest({"hrefRoot":"file:///Users/danieldaza/Documents/HTML%20pruebas%20San%20Parrilla/san-parrilla-app/","cacheDir":"file:///Users/danieldaza/Documents/HTML%20pruebas%20San%20Parrilla/san-parrilla-app/node_modules/.astro/","outDir":"file:///Users/danieldaza/Documents/HTML%20pruebas%20San%20Parrilla/san-parrilla-app/dist/","srcDir":"file:///Users/danieldaza/Documents/HTML%20pruebas%20San%20Parrilla/san-parrilla-app/src/","publicDir":"file:///Users/danieldaza/Documents/HTML%20pruebas%20San%20Parrilla/san-parrilla-app/public/","buildClientDir":"file:///Users/danieldaza/Documents/HTML%20pruebas%20San%20Parrilla/san-parrilla-app/dist/client/","buildServerDir":"file:///Users/danieldaza/Documents/HTML%20pruebas%20San%20Parrilla/san-parrilla-app/dist/server/","adapterName":"@astrojs/vercel","routes":[{"file":"","links":[],"scripts":[],"styles":[],"routeData":{"type":"page","component":"_server-islands.astro","params":["name"],"segments":[[{"content":"_server-islands","dynamic":false,"spread":false}],[{"content":"name","dynamic":true,"spread":false}]],"pattern":"^\\/_server-islands\\/([^/]+?)\\/?$","prerender":false,"isIndex":false,"fallbackRoutes":[],"route":"/_server-islands/[name]","origin":"internal","_meta":{"trailingSlash":"ignore"}}},{"file":"admin/index.html","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/admin.dFT_XuK9.css"}],"routeData":{"route":"/admin","isIndex":false,"type":"page","pattern":"^\\/admin\\/?$","segments":[[{"content":"admin","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/admin.astro","pathname":"/admin","prerender":true,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"caja/index.html","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/admin.dFT_XuK9.css"}],"routeData":{"route":"/caja","isIndex":false,"type":"page","pattern":"^\\/caja\\/?$","segments":[[{"content":"caja","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/caja.astro","pathname":"/caja","prerender":true,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"pos/index.html","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/admin.dFT_XuK9.css"}],"routeData":{"route":"/pos","isIndex":false,"type":"page","pattern":"^\\/pos\\/?$","segments":[[{"content":"pos","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/pos.astro","pathname":"/pos","prerender":true,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"index.html","links":[],"scripts":[],"styles":[{"type":"external","src":"/_astro/admin.dFT_XuK9.css"}],"routeData":{"route":"/","isIndex":true,"type":"page","pattern":"^\\/$","segments":[],"params":[],"component":"src/pages/index.astro","pathname":"/","prerender":true,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"stage":"head-inline","children":"window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };\n\t\tvar script = document.createElement('script');\n\t\tscript.defer = true;\n\t\tscript.src = '/_vercel/insights/script.js';\n\t\tvar head = document.querySelector('head');\n\t\thead.appendChild(script);\n\t"}],"styles":[],"routeData":{"type":"endpoint","isIndex":false,"route":"/_image","pattern":"^\\/_image\\/?$","segments":[[{"content":"_image","dynamic":false,"spread":false}]],"params":[],"component":"node_modules/astro/dist/assets/endpoint/generic.js","pathname":"/_image","prerender":false,"fallbackRoutes":[],"origin":"internal","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"stage":"head-inline","children":"window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };\n\t\tvar script = document.createElement('script');\n\t\tscript.defer = true;\n\t\tscript.src = '/_vercel/insights/script.js';\n\t\tvar head = document.querySelector('head');\n\t\thead.appendChild(script);\n\t"}],"styles":[],"routeData":{"route":"/api/caja","isIndex":false,"type":"endpoint","pattern":"^\\/api\\/caja\\/?$","segments":[[{"content":"api","dynamic":false,"spread":false}],[{"content":"caja","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/api/caja.js","pathname":"/api/caja","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"stage":"head-inline","children":"window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };\n\t\tvar script = document.createElement('script');\n\t\tscript.defer = true;\n\t\tscript.src = '/_vercel/insights/script.js';\n\t\tvar head = document.querySelector('head');\n\t\thead.appendChild(script);\n\t"}],"styles":[],"routeData":{"route":"/api/customers","isIndex":false,"type":"endpoint","pattern":"^\\/api\\/customers\\/?$","segments":[[{"content":"api","dynamic":false,"spread":false}],[{"content":"customers","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/api/customers.js","pathname":"/api/customers","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"stage":"head-inline","children":"window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };\n\t\tvar script = document.createElement('script');\n\t\tscript.defer = true;\n\t\tscript.src = '/_vercel/insights/script.js';\n\t\tvar head = document.querySelector('head');\n\t\thead.appendChild(script);\n\t"}],"styles":[],"routeData":{"route":"/api/orders","isIndex":false,"type":"endpoint","pattern":"^\\/api\\/orders\\/?$","segments":[[{"content":"api","dynamic":false,"spread":false}],[{"content":"orders","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/api/orders.js","pathname":"/api/orders","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"stage":"head-inline","children":"window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };\n\t\tvar script = document.createElement('script');\n\t\tscript.defer = true;\n\t\tscript.src = '/_vercel/insights/script.js';\n\t\tvar head = document.querySelector('head');\n\t\thead.appendChild(script);\n\t"}],"styles":[],"routeData":{"route":"/api/products","isIndex":false,"type":"endpoint","pattern":"^\\/api\\/products\\/?$","segments":[[{"content":"api","dynamic":false,"spread":false}],[{"content":"products","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/api/products.js","pathname":"/api/products","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}},{"file":"","links":[],"scripts":[{"stage":"head-inline","children":"window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };\n\t\tvar script = document.createElement('script');\n\t\tscript.defer = true;\n\t\tscript.src = '/_vercel/insights/script.js';\n\t\tvar head = document.querySelector('head');\n\t\thead.appendChild(script);\n\t"}],"styles":[],"routeData":{"route":"/api/specials","isIndex":false,"type":"endpoint","pattern":"^\\/api\\/specials\\/?$","segments":[[{"content":"api","dynamic":false,"spread":false}],[{"content":"specials","dynamic":false,"spread":false}]],"params":[],"component":"src/pages/api/specials.js","pathname":"/api/specials","prerender":false,"fallbackRoutes":[],"distURL":[],"origin":"project","_meta":{"trailingSlash":"ignore"}}}],"base":"/","trailingSlash":"ignore","compressHTML":true,"componentMetadata":[["/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/admin.astro",{"propagation":"none","containsHead":true}],["/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/caja.astro",{"propagation":"none","containsHead":true}],["/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/index.astro",{"propagation":"none","containsHead":true}],["/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/pos.astro",{"propagation":"none","containsHead":true}]],"renderers":[],"clientDirectives":[["idle","(()=>{var l=(n,t)=>{let i=async()=>{await(await n())()},e=typeof t.value==\"object\"?t.value:void 0,s={timeout:e==null?void 0:e.timeout};\"requestIdleCallback\"in window?window.requestIdleCallback(i,s):setTimeout(i,s.timeout||200)};(self.Astro||(self.Astro={})).idle=l;window.dispatchEvent(new Event(\"astro:idle\"));})();"],["load","(()=>{var e=async t=>{await(await t())()};(self.Astro||(self.Astro={})).load=e;window.dispatchEvent(new Event(\"astro:load\"));})();"],["media","(()=>{var n=(a,t)=>{let i=async()=>{await(await a())()};if(t.value){let e=matchMedia(t.value);e.matches?i():e.addEventListener(\"change\",i,{once:!0})}};(self.Astro||(self.Astro={})).media=n;window.dispatchEvent(new Event(\"astro:media\"));})();"],["only","(()=>{var e=async t=>{await(await t())()};(self.Astro||(self.Astro={})).only=e;window.dispatchEvent(new Event(\"astro:only\"));})();"],["visible","(()=>{var a=(s,i,o)=>{let r=async()=>{await(await s())()},t=typeof i.value==\"object\"?i.value:void 0,c={rootMargin:t==null?void 0:t.rootMargin},n=new IntersectionObserver(e=>{for(let l of e)if(l.isIntersecting){n.disconnect(),r();break}},c);for(let e of o.children)n.observe(e)};(self.Astro||(self.Astro={})).visible=a;window.dispatchEvent(new Event(\"astro:visible\"));})();"]],"entryModules":{"\u0000@astro-page:src/pages/admin@_@astro":"pages/admin.astro.mjs","\u0000@astro-page:src/pages/api/caja@_@js":"pages/api/caja.astro.mjs","\u0000@astro-page:src/pages/api/customers@_@js":"pages/api/customers.astro.mjs","\u0000@astro-page:src/pages/api/orders@_@js":"pages/api/orders.astro.mjs","\u0000@astro-page:src/pages/api/products@_@js":"pages/api/products.astro.mjs","\u0000@astro-page:src/pages/api/specials@_@js":"pages/api/specials.astro.mjs","\u0000@astro-page:src/pages/caja@_@astro":"pages/caja.astro.mjs","\u0000@astro-page:src/pages/index@_@astro":"pages/index.astro.mjs","\u0000@astro-page:src/pages/pos@_@astro":"pages/pos.astro.mjs","\u0000@astrojs-ssr-virtual-entry":"entry.mjs","\u0000@astro-renderers":"renderers.mjs","\u0000noop-middleware":"_noop-middleware.mjs","\u0000virtual:astro:actions/noop-entrypoint":"noop-entrypoint.mjs","\u0000@astro-page:node_modules/astro/dist/assets/endpoint/generic@_@js":"pages/_image.astro.mjs","\u0000@astrojs-ssr-adapter":"_@astrojs-ssr-adapter.mjs","\u0000@astrojs-manifest":"manifest_B3MY-X-I.mjs","/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/node_modules/astro/dist/assets/services/sharp.js":"chunks/sharp_BpZ-mSB2.mjs","/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/Layout.astro?astro&type=script&index=1&lang.ts":"_astro/Layout.astro_astro_type_script_index_1_lang.CN6pKSHs.js","/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/Layout.astro?astro&type=script&index=0&lang.ts":"_astro/Layout.astro_astro_type_script_index_0_lang.BRzgiJzk.js","/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/admin.astro?astro&type=script&index=0&lang.ts":"_astro/admin.astro_astro_type_script_index_0_lang.BGfx7nmc.js","/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/index.astro?astro&type=script&index=0&lang.ts":"_astro/index.astro_astro_type_script_index_0_lang.DZVC20Fm.js","/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/pos.astro?astro&type=script&index=0&lang.ts":"_astro/pos.astro_astro_type_script_index_0_lang.C7zZ3Jon.js","astro:scripts/before-hydration.js":""},"inlinedScripts":[["/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/Layout.astro?astro&type=script&index=0&lang.ts","document.addEventListener(\"DOMContentLoaded\",()=>{window.lucide&&window.lucide.createIcons()});"],["/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/admin.astro?astro&type=script&index=0&lang.ts","const r=document.getElementById(\"admin-search-dish\"),d=document.querySelectorAll(\".dish-row\");r&&r.addEventListener(\"input\",e=>{const a=e.target.value.toLowerCase().trim();d.forEach(o=>{const t=o.getAttribute(\"data-name\")||\"\";o.style.display=t.includes(a)?\"table-row\":\"none\"})});const n=document.getElementById(\"form-specials\");n&&n.addEventListener(\"submit\",async e=>{e.preventDefault();const a=document.getElementById(\"specials-sopa\").value.trim(),o=document.getElementById(\"specials-principios\").value.split(\",\").map(i=>i.trim()).filter(Boolean),t=document.getElementById(\"specials-acompanamientos\").value.split(\",\").map(i=>i.trim()).filter(Boolean),s=await(await fetch(\"/api/specials\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({sopa:a,principios:o,acompanamientos:t})})).json();s.success?alert(\"Especiales del día actualizados correctamente.\"):alert(\"Error: \"+s.error)});document.querySelectorAll(\".btn-save-price\").forEach(e=>{e.addEventListener(\"click\",async()=>{const a=e.getAttribute(\"data-id\"),o=document.querySelector(`.price-input[data-id=\"${a}\"]`),t=Number(o.value);(await(await fetch(\"/api/products\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({action:\"update_price\",id:a,price:t})})).json()).success?(e.textContent=\"✓ Guardado\",setTimeout(()=>{e.textContent=\"Actualizar\"},1500)):alert(\"Error al guardar precio\")})});document.querySelectorAll(\".btn-toggle-active\").forEach(e=>{e.addEventListener(\"click\",async()=>{const a=e.getAttribute(\"data-id\"),t=!(e.getAttribute(\"data-active\")===\"1\");(await(await fetch(\"/api/products\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({action:\"toggle_active\",id:a,is_active:t})})).json()).success?(e.setAttribute(\"data-active\",t?\"1\":\"0\"),e.textContent=t?\"✓ Activo\":\"✕ Agotado (Pausado)\",e.style.cssText=t?\"background: rgba(76, 175, 80, 0.2); color: #4CAF50; border: 1px solid rgba(76, 175, 80, 0.4);\":\"background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4);\"):alert(\"Error al actualizar disponibilidad\")})});"],["/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/index.astro?astro&type=script&index=0&lang.ts","const l=document.querySelectorAll(\".cat-filter-btn\"),c=document.querySelectorAll(\".product-card\");l.forEach(e=>{e.addEventListener(\"click\",()=>{l.forEach(t=>{t.classList.remove(\"bg-parrilla-gold\",\"text-white\",\"active\"),t.classList.add(\"bg-white\",\"text-parrilla-ivory\")}),e.classList.add(\"bg-parrilla-gold\",\"text-white\",\"active\"),e.classList.remove(\"bg-white\",\"text-parrilla-ivory\");const a=e.getAttribute(\"data-category\");c.forEach(t=>{const r=t.getAttribute(\"data-cat\");a===\"all\"||r===a?t.style.display=\"flex\":t.style.display=\"none\"})})});"]],"assets":["/_astro/admin.dFT_XuK9.css","/hero-bg.jpg","/logo.png","/_astro/Layout.astro_astro_type_script_index_1_lang.CN6pKSHs.js","/_astro/pos.astro_astro_type_script_index_0_lang.C7zZ3Jon.js","/admin/index.html","/caja/index.html","/pos/index.html","/index.html"],"buildFormat":"directory","checkOrigin":true,"allowedDomains":[],"actionBodySizeLimit":1048576,"serverIslandNameMap":[],"key":"AId71i2i8H1iPbH53K16Dp9Rx2oJMwkdYI5ANgOpm80="});
if (manifest.sessionConfig) manifest.sessionConfig.driverModule = null;

export { manifest };
