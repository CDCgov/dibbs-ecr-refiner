import { test, expect } from './fixtures';
import { clearUserNotifications } from './db';

test.describe('Notification banners', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearUserNotifications();
    await configurationsPage.goto();
  });

  test.afterEach(async () => {
    await clearUserNotifications();
  });

  test('Both an app update banner and a TES update banner are displayed to the user', async ({
    page,
  }) => {
    // app updates
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'View app updates' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Dismiss TES updates notification' })
    ).toBeVisible();

    // tes updates
    await expect(
      page.getByText('A new TES update was published.')
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'View app updates' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Dismiss TES updates notification' })
    ).toBeVisible();
  });

  test('Banner is dismissed upon clicking the "X" button', async ({ page }) => {
    const appUpdateText = page.getByText(
      'There are new updates to eCR Refiner.'
    );
    const appUpdateBannerButton = page.getByRole('button', {
      name: 'Dismiss app updates notification',
    });

    const tesUpdateText = page.getByText('A new TES update was published.');
    const tesUpdateBannerButton = page.getByRole('button', {
      name: 'Dismiss TES updates notification',
    });

    await expect(appUpdateText).toBeVisible();
    await appUpdateBannerButton.click();
    await expect(appUpdateText).not.toBeVisible();

    await expect(tesUpdateText).toBeVisible();
    await tesUpdateBannerButton.click();
    await expect(tesUpdateText).not.toBeVisible();

    // make sure they're gone on a refresh
    await page.reload();
    await expect(
      page.getByRole('heading', { name: 'Configurations', level: 1 })
    ).toBeVisible();
    await expect(appUpdateText).not.toBeVisible();
    await expect(tesUpdateText).not.toBeVisible();
  });

  test('clicking "view updates" button dismisses the banner', async ({
    page,
    configurationsPage,
  }) => {
    const bannerText = page.getByText('There are new updates to eCR Refiner.');

    await expect(bannerText).toBeVisible();

    await page.getByRole('link', { name: 'View app updates' }).click();
    await expect(
      page.getByRole('heading', { name: 'App updates' })
    ).toBeVisible();

    await configurationsPage.goto();
    await expect(bannerText).not.toBeVisible();
  });
});
