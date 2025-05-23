/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const uswdsIncludePaths = [
  'node_modules/@uswds',
  'node_modules/@uswds/uswds/packages',
];

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: 'tests/setup.ts',
  },
  css: {
    preprocessorOptions: {
      scss: {
        quietDeps: true, // tons of deprecation warnings caused by uswds
        loadPaths: uswdsIncludePaths,
      },
    },
    modules: {
      localsConvention: 'camelCaseOnly',
    },
  },
  server: {
    host: true,
    strictPort: true,
    port: 8081,
    proxy: {
      '/api': {
        target: 'http://message-refiner-service:8080',
        changeOrigin: true,
      },
    },
  },
});
