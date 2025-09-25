import { test, expect } from '@playwright/test';

test.describe('Viewing the application without logging in', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8081');
  })

  test('homepage has expected title and content', async ({ page }) => {
    await expect(page).toHaveTitle(/DIBBs eCR Refiner/);
  });

  test('should show a login button', async ({ page }) => {
    await expect(page.getByText('Log in')).toBeVisible();
  });
})
