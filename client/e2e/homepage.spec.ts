import { test, expect } from '@playwright/test';
import { login, logout } from './utils';

test.describe('Viewing the application without logging in', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('homepage has expected title and content', async ({ page }) => {
    await expect(page).toHaveTitle(/DIBBs eCR Refiner/);
  });

  test('should show a login button', async ({ page }) => {
    await expect(page.getByText('Log in')).toBeVisible();
  });
});

test.describe('Viewing the application when logged in', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should be able to see the configuration tab', async ({ page }) => {
    await expect(
      page.getByText('Your reportable condition configurations')
    ).toBeVisible();
  });
});
