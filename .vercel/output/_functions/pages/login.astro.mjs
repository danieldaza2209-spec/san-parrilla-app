import { e as createComponent, k as renderComponent, r as renderTemplate, h as createAstro, m as maybeRenderHead, g as addAttribute, l as renderScript } from '../chunks/astro/server_DwdL0MGX.mjs';
import 'piccolore';
import { $ as $$BaseLayout } from '../chunks/BaseLayout_B8PTuIAK.mjs';
import { S as SESSION_COOKIE, v as verifySessionToken, h as homeForRole, i as isAuthConfigured } from '../chunks/auth_CUmhD9Do.mjs';
export { renderers } from '../renderers.mjs';

const $$Astro = createAstro();
const $$Login = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Login;
  const token = Astro2.cookies.get(SESSION_COOKIE)?.value;
  const session = token ? verifySessionToken(token) : null;
  if (session) return Astro2.redirect(homeForRole(session.role));
  const configured = isAuthConfigured();
  const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "title": "Acceso del personal | San Parrilla", "noindex": true }, { "default": async ($$result2) => renderTemplate` ${maybeRenderHead()}<main class="flex-1 flex items-center justify-center px-4 py-10 bg-gradient-to-b from-slate-100/70 to-parrilla-dark"> <div class="w-full max-w-sm"> <div class="text-center mb-6"> <img src="/logo.png" alt="San Parrilla" class="h-16 w-auto mx-auto rounded-full ring-2 ring-parrilla-gold/30 mb-3"> <h1 class="font-display font-black text-2xl text-parrilla-ivory">Acceso del personal</h1> <p class="text-xs text-parrilla-muted mt-1">Ingresa tu PIN para abrir tu herramienta de trabajo.</p> </div> <div class="bg-white rounded-2xl border border-parrilla-border shadow-xl p-5"> ${!configured && renderTemplate`<div class="mb-4 text-xs font-semibold text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">
El acceso aún no está configurado en el servidor. Avisa al administrador.
</div>`} <form id="login-form" class="space-y-4" autocomplete="off"> <div> <label for="pin" class="block text-xs font-bold text-parrilla-gold uppercase tracking-wider mb-1.5">PIN o contraseña</label> <input id="pin" name="pin" type="password" inputmode="numeric" autocomplete="current-password" maxlength="64" required${addAttribute(!configured, "disabled")} class="w-full px-4 py-3 bg-white rounded-xl border border-parrilla-border text-center text-2xl tracking-[0.5em] font-bold font-mono text-parrilla-ivory focus:border-parrilla-gold outline-none" placeholder="••••"> </div> <div class="grid grid-cols-3 gap-2" id="keypad"> ${keys.map((k) => renderTemplate`<button type="button"${addAttribute(k, "data-key")} class="py-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 active:scale-95 text-xl font-bold text-parrilla-ivory border border-parrilla-border transition">${k}</button>`)} <button type="button" data-action="clear" class="py-3.5 rounded-xl bg-slate-100 hover:bg-red-50 active:scale-95 text-xs font-bold text-parrilla-muted hover:text-red-500 border border-parrilla-border transition">Borrar</button> <button type="button" data-key="0" class="py-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 active:scale-95 text-xl font-bold text-parrilla-ivory border border-parrilla-border transition">0</button> <button type="button" data-action="back" class="py-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 active:scale-95 text-lg font-bold text-parrilla-muted border border-parrilla-border transition" aria-label="Borrar último dígito">⌫</button> </div> <p id="login-error" class="hidden text-xs font-semibold text-red-600 bg-red-50 border border-red-200 rounded-xl p-2.5 text-center" role="alert"></p> <button id="login-submit" type="submit"${addAttribute(!configured, "disabled")} class="w-full py-3.5 rounded-xl bg-parrilla-gold hover:bg-parrilla-goldLight text-white font-display font-black text-base shadow-md transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed">
Entrar
</button> </form> </div> <p class="text-center mt-5"> <a href="/" class="text-xs font-medium text-parrilla-muted hover:text-parrilla-gold transition">← Volver a la carta</a> </p> </div> </main> ${renderScript($$result2, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/login.astro?astro&type=script&index=0&lang.ts")} ` })}`;
}, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/login.astro", void 0);

const $$file = "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/pages/login.astro";
const $$url = "/login";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$Login,
  file: $$file,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
