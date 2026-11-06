import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel';

export default defineConfig({
  output: 'server',
  security: {
    checkOrigin: false,
  },
  build: {
    inlineStylesheets: 'always',
  },
  adapter: vercel({
    webAnalytics: {
      enabled: true,
    },
  }),
  integrations: [tailwind({
    applyBaseStyles: false,
  })],
});
