import { test, expect } from './fixtures';
import { resetUserNotificationState } from './db';

test.describe('App update notifications', () => {
  const latestReleaseCreatedAt = '2099-05-05T15:00:00.000Z';

  test.beforeEach(async ({ page, configurationsPage }) => {
    await resetUserNotificationState();

    await page.route(
      (url) => url.pathname === '/api/releases/getReleases/',
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            releases: [
              {
                id: 'release-1',
                created_at: latestReleaseCreatedAt,
                name: 'Test release',
                prerelease: false,
                url: 'https://example.com',
                release_notes: [
                  {
                    id: 'note-1',
                    header: 'Summary',
                    content: 'Test release summary.',
                  },
                ],
              },
            ],
          }),
        });
      }
    );

    await configurationsPage.goto();
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

  test('dismiss X removes banner', async ({ page, configurationsPage }) => {
    await page.getByRole('button', { name: 'Dismiss notification' }).click();

    // Ensure banner is gone
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).not.toBeVisible();

    await expect(page).toHaveURL(/\/configurations/);
    await configurationsPage.checkBannerIsDismissed();
  });

  test('view update removes banner', async ({ page, configurationsPage }) => {
    await page.getByRole('link', { name: 'View updates' }).click();

    // Ensure banner is gone
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).not.toBeVisible();

    await expect(
      page.getByRole('heading', { name: 'App updates', exact: true, level: 1 })
    ).toBeVisible();
    await configurationsPage.checkBannerIsDismissed();
  });
});
