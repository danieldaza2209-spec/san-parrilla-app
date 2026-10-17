import { e as createComponent, g as addAttribute, l as renderScript, o as renderHead, r as renderTemplate, p as renderSlot, h as createAstro } from './astro/server_CKkv12kC.mjs';
import 'piccolore';
import 'clsx';
/* empty css                         */

const $$Astro = createAstro();
const $$Layout = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Layout;
  const {
    title = "Restaurante San Parrilla | Men\xFA Digital & Brasas",
    description = "El mejor sabor a la parrilla, carnes selectas, men\xFA del d\xEDa y picadas especiales en San Parrilla.",
    showNav = true
  } = Astro2.props;
  return renderTemplate`<html lang="es" class="scroll-smooth"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link rel="icon" type="image/png" href="/logo.png"><title>${title}</title><meta name="description"${addAttribute(description, "content")}><!-- Google Fonts: Outfit & Inter --><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800;900&display=swap" rel="stylesheet"><!-- Lucide Icons -->${renderScript($$result, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/Layout.astro?astro&type=script&index=0&lang.ts")}${renderHead()}</head> <body class="bg-parrilla-dark text-parrilla-ivory min-h-screen flex flex-col selection:bg-parrilla-gold selection:text-parrilla-dark"> ${showNav && renderTemplate`<header class="sticky top-0 z-40 bg-parrilla-surface/90 backdrop-blur-md border-b border-parrilla-border no-print"> <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between"> <!-- Brand --> <a href="/" class="flex items-center gap-3 group"> <img src="/logo.png" alt="San Parrilla Logo" class="h-10 w-auto rounded-full ring-2 ring-parrilla-gold/40 group-hover:ring-parrilla-gold transition"> <div class="flex flex-col"> <span class="font-display font-extrabold text-xl tracking-tight leading-none text-parrilla-ivory">
SAN <span class="text-parrilla-gold">PARRILLA</span> </span> <span class="text-[10px] tracking-widest text-parrilla-muted uppercase font-medium">Sazón & Fogón</span> </div> </a> <!-- Navigation Links --> <nav class="hidden md:flex items-center gap-1 bg-parrilla-dark/60 p-1.5 rounded-full border border-parrilla-border text-sm"> <a href="/" class="px-4 py-1.5 rounded-full text-parrilla-ivory hover:text-parrilla-gold hover:bg-parrilla-surface transition font-medium">
🍽️ Menú Carta
</a> <a href="/pos" class="px-4 py-1.5 rounded-full bg-parrilla-gold/10 text-parrilla-gold border border-parrilla-gold/30 hover:bg-parrilla-gold hover:text-parrilla-dark font-semibold transition">
⚡ Punto de Venta (POS)
</a> <a href="/caja" class="px-4 py-1.5 rounded-full text-parrilla-ivory hover:text-parrilla-gold hover:bg-parrilla-surface transition font-medium">
💵 Cuadre de Caja
</a> <a href="/admin" class="px-4 py-1.5 rounded-full text-parrilla-ivory hover:text-parrilla-gold hover:bg-parrilla-surface transition font-medium">
📊 Métricas & Menú
</a> </nav> <!-- Right Quick Actions --> <div class="flex items-center gap-3"> <a href="https://wa.me/573183821787" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 bg-parrilla-gold hover:bg-parrilla-goldLight text-parrilla-dark font-bold text-xs sm:text-sm px-3.5 py-2 rounded-lg shadow-md hover:shadow-parrilla-gold/20 transition active:scale-95"> <i data-lucide="phone" class="w-4 h-4"></i> <span class="hidden sm:inline">WhatsApp</span> </a> <a href="/pos" class="md:hidden inline-flex items-center justify-center p-2 rounded-lg bg-parrilla-surface border border-parrilla-border text-parrilla-gold"> <i data-lucide="shopping-bag" class="w-5 h-5"></i> </a> </div> </div> </header>`} <main class="flex-1"> ${renderSlot($$result, $$slots["default"])} </main> <footer class="bg-parrilla-surface border-t border-parrilla-border py-8 text-center text-xs text-parrilla-muted no-print"> <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4"> <div class="flex items-center gap-2"> <span class="font-display font-bold text-parrilla-gold text-sm">SAN PARRILLA</span> <span>•</span> <span>Tradición & Sazón Casero</span> </div> <div class="flex items-center gap-6"> <a href="/" class="hover:text-parrilla-gold transition">Menú</a> <a href="/pos" class="hover:text-parrilla-gold transition">POS</a> <a href="/caja" class="hover:text-parrilla-gold transition">Caja</a> <a href="/admin" class="hover:text-parrilla-gold transition">Administración</a> </div> <p>© ${(/* @__PURE__ */ new Date()).getFullYear()} San Parrilla. Todos los derechos reservados.</p> </div> </footer> ${renderScript($$result, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/Layout.astro?astro&type=script&index=1&lang.ts")} </body> </html>`;
}, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/Layout.astro", void 0);

export { $$Layout as $ };
