import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  globalTeardown: './e2e/setup/global-teardown.ts',
  testDir: './e2e',
  timeout: process.env.CI ? 60 * 1000 : 30 * 1000,
  expect: {
    timeout: 10 * 1000,
  },
  retries: process.env.CI ? 2 : 0,
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
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'e2e',
      testMatch: /.*\.spec\.ts/,
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/.auth/user.json',
      },
    },
  ],
});
