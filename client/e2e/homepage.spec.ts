import { test, expect } from '@playwright/test';

test('homepage has expected title and content', async ({ page }) => {
  await page.goto('http://localhost:8081');
  await expect(page).toHaveTitle(/DIBBs eCR Refiner/);
});

test('should show a login button', async ({ page }) => {
  await page.goto('http://localhost:8081');
  await expect(page.getByRole('button', { name: /log in/i })).toBeVisible();
});
