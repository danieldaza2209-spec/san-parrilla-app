/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        parrilla: {
          dark: '#18110e',
          surface: '#261b16',
          card: '#201612',
          cardHover: '#2d1f19',
          border: 'rgba(121, 85, 72, 0.35)',
          gold: '#FFD700',
          goldLight: '#ffe240',
          ivory: '#FFFFF0',
          accent: '#4CAF50',
          muted: '#a89f91',
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
