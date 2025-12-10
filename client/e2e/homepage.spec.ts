import { test as loggedInTest, expect } from './fixtures/fixtures';
import test from '@playwright/test';
import { login } from './utils';

loggedInTest.describe('Viewing the application sign in content', () => {
  loggedInTest(
    'should be able to see the configuration page, and both testing and configuration tabs',
    async ({ page, makeAxeBuilder }) => {
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
      await expect(makeAxeBuilder).toHaveNoAxeViolations();
    }
  );
  // import and use the base test from Playwright since we need to log in and out
  test('should show the username in the top right and able to logout', async ({
    page,
  }) => {
    await login(page);
    // 1️⃣ Locate the refiner button and click it
    const refinerButton = page.locator('button', {
      hasText: 'refiner (SDDH)',
    });
    await expect(refinerButton).toBeVisible();
    await refinerButton.click();

    // 2️⃣ Assert the logout link is visible
    const logoutLink = page.locator('a[href="/api/logout"]', {
      hasText: 'Log out',
    });
    await expect(logoutLink).toBeVisible();

    // 3️⃣ Click the logout link
    await logoutLink.click();

    // homepage should have the relevant content
    await expect(page).toHaveTitle(/DIBBs eCR Refiner/);
    await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
  });
});
