/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

const uswdsIncludePaths = [
  'node_modules/@uswds',
  'node_modules/@uswds/uswds/packages',
];

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@components': path.resolve(__dirname, 'src/components'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    // prevent Vitest from running Playwright tests or dependency's tests.
    exclude: ['e2e', 'e2e/**/*', 'node_modules'],
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
    watch: {
      ignored: ['**/e2e/**'],
    },
    host: true,
    strictPort: true,
    port: 8081,
    proxy: {
      '/api': {
        target: 'http://server:8080',
        changeOrigin: true,
      },
    },
  },
});
