import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    // prevent Vitest from running Playwright tests or dependency's tests.
    exclude: ['e2e', 'e2e/**/*', 'node_modules'],
    setupFiles: 'tests/setup.ts',
  },
});
