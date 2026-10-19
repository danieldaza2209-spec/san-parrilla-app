/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        parrilla: {
          dark: '#F8FAFC',        // Canvas / fondo general claro (soft slate-50)
          surface: '#FFFFFF',     // Superficies, tarjetas, barra y paneles en blanco puro
          card: '#FFFFFF',        // Tarjetas
          cardHover: '#F1F5F9',   // Hover suave
          border: '#E2E8F0',      // Bordes limpios y definidos (slate-200)
          gold: '#C2410C',        // Acento fuego / asador tostado (Orange-700 / brasa cálida)
          goldLight: '#9A3412',   // Hover más intenso (Orange-800)
          ivory: '#0F172A',       // Texto principal oscuro (Slate-900 / máxima legibilidad)
          accent: '#15803D',      // Verde fresco (Green-700 para éxito y WhatsApp)
          muted: '#64748B',       // Texto secundario y etiquetas (Slate-500)
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
