import { renderers } from './renderers.mjs';
import { c as createExports, s as serverEntrypointModule } from './chunks/_@astrojs-ssr-adapter_Cr5axppe.mjs';
import { manifest } from './manifest_DKtgT8ig.mjs';

const serverIslandMap = new Map();;

const _page0 = () => import('./pages/_image.astro.mjs');
const _page1 = () => import('./pages/admin.astro.mjs');
const _page2 = () => import('./pages/api/caja.astro.mjs');
const _page3 = () => import('./pages/api/customers.astro.mjs');
const _page4 = () => import('./pages/api/orders.astro.mjs');
const _page5 = () => import('./pages/api/products.astro.mjs');
const _page6 = () => import('./pages/api/specials.astro.mjs');
const _page7 = () => import('./pages/caja.astro.mjs');
const _page8 = () => import('./pages/pos.astro.mjs');
const _page9 = () => import('./pages/index.astro.mjs');
const pageMap = new Map([
    ["node_modules/astro/dist/assets/endpoint/generic.js", _page0],
    ["src/pages/admin.astro", _page1],
    ["src/pages/api/caja.js", _page2],
    ["src/pages/api/customers.js", _page3],
    ["src/pages/api/orders.js", _page4],
    ["src/pages/api/products.js", _page5],
    ["src/pages/api/specials.js", _page6],
    ["src/pages/caja.astro", _page7],
    ["src/pages/pos.astro", _page8],
    ["src/pages/index.astro", _page9]
]);

const _manifest = Object.assign(manifest, {
    pageMap,
    serverIslandMap,
    renderers,
    actions: () => import('./noop-entrypoint.mjs'),
    middleware: () => import('./_noop-middleware.mjs')
});
const _args = {
    "middlewareSecret": "75f83c33-db7a-4f81-951d-1c7e8a359a72",
    "skewProtection": false
};
const _exports = createExports(_manifest, _args);
const __astrojsSsrVirtualEntry = _exports.default;
const _start = 'start';
if (Object.prototype.hasOwnProperty.call(serverEntrypointModule, _start)) ;

export { __astrojsSsrVirtualEntry as default, pageMap };
