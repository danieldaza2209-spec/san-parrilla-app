import { e as createComponent, g as addAttribute, r as renderTemplate, l as renderScript, p as renderHead, o as renderSlot, h as createAstro } from './astro/server_DwdL0MGX.mjs';
import 'piccolore';
import 'clsx';
/* empty css                         */

const $$Astro = createAstro();
const $$BaseLayout = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$BaseLayout;
  const {
    title = "San Parrilla",
    description = "El mejor sabor a la parrilla, carnes selectas, men\xFA del d\xEDa y picadas especiales en San Parrilla.",
    noindex = false
  } = Astro2.props;
  return renderTemplate`<html lang="es" class="scroll-smooth"> <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link rel="icon" type="image/png" href="/logo.png"><title>${title}</title><meta name="description"${addAttribute(description, "content")}>${noindex && renderTemplate`<meta name="robots" content="noindex, nofollow, noarchive">`}<!-- Google Fonts: Outfit & Inter --><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800;900&display=swap" rel="stylesheet"><!-- Lucide Icons -->${renderScript($$result, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/BaseLayout.astro?astro&type=script&index=0&lang.ts")}${renderHead()}</head> <body class="bg-parrilla-dark text-parrilla-ivory min-h-screen flex flex-col selection:bg-parrilla-gold selection:text-white"> ${renderSlot($$result, $$slots["default"])} ${renderScript($$result, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/BaseLayout.astro?astro&type=script&index=1&lang.ts")} </body> </html>`;
}, "/Users/danieldaza/Documents/HTML pruebas San Parrilla/san-parrilla-app/src/layouts/BaseLayout.astro", void 0);

export { $$BaseLayout as $ };
