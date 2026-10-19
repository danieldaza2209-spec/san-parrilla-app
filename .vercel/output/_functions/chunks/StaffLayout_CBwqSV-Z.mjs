import { e as createComponent, k as renderComponent, r as renderTemplate, h as createAstro, m as maybeRenderHead, g as addAttribute, o as renderSlot } from './astro/server_DwdL0MGX.mjs';
import 'piccolore';
import { $ as $$BaseLayout } from './BaseLayout_B8PTuIAK.mjs';
import { d as getActiveCashRegister } from './db_Be_7xi3m.mjs';
import { R as ROLE_ADMIN, d as ROLE_LABELS } from './auth_CUmhD9Do.mjs';

const $$Astro = createAstro();
const $$StaffLayout = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$StaffLayout;
  const { title = "Personal | San Parrilla" } = Astro2.props;
  const user = Astro2.locals.user;
  const isAdmin = user?.role === ROLE_ADMIN;
  const pathname = Astro2.url.pathname.replace(/\/+$/, "") || "/";
  const cashOpen = Boolean(getActiveCashRegister());
  const navItems = [
    { href: "/pos", label: "Punto de Venta", icon: "zap", show: true },
    { href: "/caja", label: "Caja", icon: "wallet", show: true },
    { href: "/admin", label: "Administraci\xF3n", icon: "bar-chart-3", show: isAdmin }
  ].filter((item) => item.show);
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "title": title, "noindex": true }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<header class="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-parrilla-border no-print"> <div class="max-w-[1600px] mx-auto px-3 sm:px-4 h-14 flex items-center justify-between gap-3"> <div class="flex items-center gap-3 min-w-0"> <img src="/logo.png" alt="San Parrilla" class="h-9 w-auto rounded-full ring-2 ring-parrilla-gold/30"> <nav class="flex items-center gap-1 bg-slate-100/90 p-1 rounded-full border border-parrilla-border text-sm"> ${navItems.map((item) => {
    const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
    return renderTemplate`<a${addAttribute(item.href, "href")}${addAttribute([
      "px-3 sm:px-4 py-1.5 rounded-full font-semibold transition inline-flex items-center gap-1.5",
      active ? "bg-parrilla-gold text-white shadow-sm" : "text-parrilla-ivory hover:text-parrilla-gold hover:bg-white"
    ], "class:list")}> <i${addAttribute(item.icon, "data-lucide")} class="w-4 h-4"></i> <span class="hidden sm:inline">${item.label}</span> </a>`;
  })} </nav> </div> <div class="flex items-center gap-2 sm:gap-3"> <span${addAttribute([
    "hidden md:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border",
    cashOpen ? "bg-green-50 text-parrilla-accent border-green-200" : "bg-red-50 text-red-600 border-red-200"
  ], "class:list")}> <span${addAttribute(["w-2 h-2 rounded-full", cashOpen ? "bg-parrilla-accent animate-pulse" : "bg-red-500"], "class:list")}></span> ${cashOpen ? "Caja abierta" : "Caja cerrada"} </span> <span class="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold text-parrilla-muted"> <i data-lucide="user-round" class="w-4 h-4"></i> ${user ? ROLE_LABELS[user.role] : ""} </span> <form method="POST" action="/api/auth/logout"> <button type="submit" class="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg bg-slate-100 hover:bg-red-50 text-parrilla-muted hover:text-red-500 border border-parrilla-border transition" title="Cerrar sesión"> <i data-lucide="log-out" class="w-4 h-4"></i> <span class="hidden sm:inline">Salir</span> </button> </form> </div> </div> </header> <main class="flex-1"> ${renderSlot($$result2, $$slots["default"])} </main> ` })}`;
}, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/StaffLayout.astro", void 0);

export { $$StaffLayout as $ };
