import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
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

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:8081',
    // always reuse the server if it's already running
    reuseExistingServer: true,
    env: {
      // if VITE_ENV is undefined, default to an empty string ''
      VITE_ENV: process.env.VITE_ENV ?? '',
      // if VITE_GIT_BRANCH is undefined, default to an empty string ''
      VITE_GIT_BRANCH: process.env.VITE_GIT_BRANCH ?? '',
    },
  },
});
