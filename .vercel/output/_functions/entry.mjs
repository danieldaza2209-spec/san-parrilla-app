import { renderers } from './renderers.mjs';
import { c as createExports, s as serverEntrypointModule } from './chunks/_@astrojs-ssr-adapter_CeMPkKFr.mjs';
import { manifest } from './manifest_BLDsj4K4.mjs';

const serverIslandMap = new Map();;

const _page0 = () => import('./pages/_image.astro.mjs');
const _page1 = () => import('./pages/admin.astro.mjs');
const _page2 = () => import('./pages/api/auth/login.astro.mjs');
const _page3 = () => import('./pages/api/auth/logout.astro.mjs');
const _page4 = () => import('./pages/api/caja.astro.mjs');
const _page5 = () => import('./pages/api/customers.astro.mjs');
const _page6 = () => import('./pages/api/launcher.astro.mjs');
const _page7 = () => import('./pages/api/orders.astro.mjs');
const _page8 = () => import('./pages/api/products.astro.mjs');
const _page9 = () => import('./pages/api/specials.astro.mjs');
const _page10 = () => import('./pages/caja.astro.mjs');
const _page11 = () => import('./pages/login.astro.mjs');
const _page12 = () => import('./pages/pos.astro.mjs');
const _page13 = () => import('./pages/index.astro.mjs');
const pageMap = new Map([
    ["node_modules/astro/dist/assets/endpoint/generic.js", _page0],
    ["src/pages/admin.astro", _page1],
    ["src/pages/api/auth/login.js", _page2],
    ["src/pages/api/auth/logout.js", _page3],
    ["src/pages/api/caja.js", _page4],
    ["src/pages/api/customers.js", _page5],
    ["src/pages/api/launcher.js", _page6],
    ["src/pages/api/orders.js", _page7],
    ["src/pages/api/products.js", _page8],
    ["src/pages/api/specials.js", _page9],
    ["src/pages/caja.astro", _page10],
    ["src/pages/login.astro", _page11],
    ["src/pages/pos.astro", _page12],
    ["src/pages/index.astro", _page13]
]);

const _manifest = Object.assign(manifest, {
    pageMap,
    serverIslandMap,
    renderers,
    actions: () => import('./noop-entrypoint.mjs'),
    middleware: () => import('./_astro-internal_middleware.mjs')
});
const _args = {
    "middlewareSecret": "a921ab5f-04ef-4c83-ae52-f2c8e426d8aa",
    "skewProtection": false
};
const _exports = createExports(_manifest, _args);
const __astrojsSsrVirtualEntry = _exports.default;
const _start = 'start';
if (Object.prototype.hasOwnProperty.call(serverEntrypointModule, _start)) ;

export { __astrojsSsrVirtualEntry as default, pageMap };
