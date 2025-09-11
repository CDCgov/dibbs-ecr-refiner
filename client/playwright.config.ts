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
                baseURL: 'http://localhost:8081', // Change port if needed for local dev server
                screenshot: 'only-on-failure',
                video: 'retain-on-failure',
        },
        projects: [
                {
                        name: 'Chromium',
                        use: { ...devices['Desktop Chrome'] },
                },
                {
                        name: 'Firefox',
                        use: { ...devices['Desktop Firefox'] },
                },
                {
                        name: 'WebKit',
                        use: { ...devices['Desktop Safari'] },
                },
        ],
});
