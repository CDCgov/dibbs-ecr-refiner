import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30 * 1000,
  expect: {
    timeout: 10000,
  },
  forbidOnly: !!process.env.CI,
  workers: 1,
  reporter: [['html', { open: 'never' }]],
  use: {
    trace: 'on-first-retry',
    baseURL: 'http://localhost:8081',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'Chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
