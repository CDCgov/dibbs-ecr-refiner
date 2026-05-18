import { test, expect } from './fixtures';
import { clearUserNotifications, deleteAllConfigurations } from './db';

test.describe('App update notifications', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearUserNotifications();
    await deleteAllConfigurations();

    await configurationsPage.goto();
  });

  test.afterEach(async () => {
    await clearUserNotifications();
    await deleteAllConfigurations();
  });

  test('shows app update banner when latest release has not been acknowledged', async ({
    page,
  }) => {
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).toBeVisible();

    await expect(
      page.getByRole('link', { name: 'View updates' })
    ).toBeVisible();

    await expect(
      page.getByRole('button', { name: 'Dismiss notification' })
    ).toBeVisible();
  });

  test('clicking "view updates" button dismisses the banner', async ({
    page,
    configurationsPage,
  }) => {
    const bannerText = page.getByText('There are new updates to eCR Refiner.');

    await expect(bannerText).toBeVisible();

    await page.getByRole('link', { name: 'View updates' }).click();
    await expect(
      page.getByRole('heading', { name: 'App updates' })
    ).toBeVisible();
    await configurationsPage.goto();
    await expect(bannerText).not.toBeVisible();
  });

  test('clicking "X" button dismisses the banner', async ({ page }) => {
    const bannerText = page.getByText('There are new updates to eCR Refiner.');
    await expect(bannerText).toBeVisible();
    await page.getByRole('button', { name: 'Dismiss notification' }).click();
    await expect(bannerText).not.toBeVisible();
  });
});
