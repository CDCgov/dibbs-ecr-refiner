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
    await test.step('App banner', async () => {
      const appText = 'There are new updates to eCR Refiner.';
      await expect(page.getByText(appText, { exact: true })).toBeVisible();
      await expect(
        page.getByRole('link', { name: 'View updates for app' })
      ).toBeVisible();
      await expect(
        page.getByRole('button', {
          name: `Dismiss notification for ${appText}`,
        })
      ).toBeVisible();
    });

    await test.step('TES banner', async () => {
      const tesText = 'A new TES update was published.';
      await expect(page.getByText(tesText, { exact: true })).toBeVisible();
      await expect(
        page.getByRole('link', { name: 'View updates for TES' })
      ).toBeVisible();
      await expect(
        page.getByRole('button', {
          name: `Dismiss notification for ${tesText}`,
        })
      ).toBeVisible();
    });
  });

  test('Banner is dismissed upon clicking the "X" button', async ({ page }) => {
    const appText = 'There are new updates to eCR Refiner.';
    const appUpdateText = page.getByText(appText, { exact: true });
    const appUpdateBannerButton = page.getByRole('button', {
      name: `Dismiss notification for ${appText}`,
    });

    const tesText = 'A new TES update was published.';
    const tesUpdateText = page.getByText(tesText, { exact: true });
    const tesUpdateBannerButton = page.getByRole('button', {
      name: `Dismiss notification for ${tesText}`,
    });

    await expect(appUpdateText).toBeVisible();
    await appUpdateBannerButton.click();
    await expect(appUpdateText).not.toBeVisible();

    await expect(tesUpdateText).toBeVisible();
    await tesUpdateBannerButton.click();
    await expect(tesUpdateText).not.toBeVisible();

    // make sure they're both gone on a refresh
    await page.reload();
    await expect(
      page.getByRole('heading', { name: 'Configurations', level: 1 })
    ).toBeVisible();
    await expect(appUpdateText).not.toBeVisible();
    await expect(tesUpdateText).not.toBeVisible();
  });

  test('Clicking "view updates" button dismisses the banner', async ({
    page,
    configurationsPage,
  }) => {
    await test.step('App banner', async () => {
      const appBannerText = page.getByText(
        'There are new updates to eCR Refiner.',
        {
          exact: true,
        }
      );

      await expect(appBannerText).toBeVisible();

      await page.getByRole('link', { name: 'View updates for app' }).click();
      await expect(
        page.getByRole('heading', { name: 'App updates' })
      ).toBeVisible();

      await configurationsPage.goto();
      await expect(appBannerText).not.toBeVisible();
    });

    await test.step('TES banner', async () => {
      const tesBannerText = page.getByText('A new TES update was published.', {
        exact: true,
      });
      await expect(tesBannerText).toBeVisible();

      await page.getByRole('link', { name: 'View updates for TES' }).click();
      await expect(
        page.getByRole('heading', { name: 'TES Updates' })
      ).toBeVisible();

      await configurationsPage.goto();
      await expect(tesBannerText).not.toBeVisible();
    });
  });
});
