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
  test('should be able to see the configuration page, and both testing and configuration tabs', async ({
    browser,
    page,
  }) => {
    const context = await browser.newContext();
    page = await context.newPage();
    await expect(
      page.getByRole('link', { name: 'Provide Feedback' })
    ).toBeHidden();
    await login(page);
    await expect(
      page.getByRole('link', { name: 'Provide Feedback' })
    ).toBeVisible();
    await expect(page.getByRole('link', { name: 'Testing' })).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Configurations' })
    ).toBeVisible();
    await expect(
      page.getByText('Your reportable condition configurations')
    ).toBeVisible();
    await logout(page);
    await page.close();
  });

  test('should show the username in the top right and able to logout', async ({
    page,
  }) => {
    await login(page);

    // 1️⃣ Locate the refiner button and click it
    const refinerButton = page.locator('button', { hasText: 'refiner (SDDH)' });
    await expect(refinerButton).toBeVisible();
    await refinerButton.click();

    // 2️⃣ Assert the logout link is visible
    const logoutLink = page.locator('a[href="/api/logout"]', {
      hasText: 'Log out',
    });
    await expect(logoutLink).toBeVisible();

    // 3️⃣ Click the logout link
    await logoutLink.click();
    await expect(page).toHaveTitle(/DIBBs eCR Refiner/);
    await expect(page.getByText('Log in')).toBeVisible();
  });
});
