import { test, expect } from './fixtures';
import { deleteAllConfigurations } from './db';

test.describe('App update notifications', () => {
  const latestReleaseCreatedAt = '2099-05-05T15:00:00.000Z';

  test.beforeEach(async ({ page, configurationsPage }) => {
    await deleteAllConfigurations();

    await page.route(
      (url) =>
        url.pathname === '/api/releases/getReleases' ||
        url.pathname === '/api/releases/getReleases/' ||
        url.pathname === '/api/releases' ||
        url.pathname === '/api/releases/',
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

    await page.route(/\/api\/v1\/notifications\/?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '5deb43c2-6a82-4052-9918-616e01d255c7',
          username: 'tester',
          jurisdiction_id: 'JD-1',
          notifications: {
            most_recent_app_update: {
              date_acknowledged: latestReleaseCreatedAt,
            },
          },
        }),
      });
    });

    await configurationsPage.goto();
  });

  test.afterEach(async () => {
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

  test('dismiss X removes banner', async ({ page }) => {
    await page.getByRole('button', { name: 'Dismiss notification' }).click();

    // Ensure banner is gone
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).not.toBeVisible();

    await expect(page).toHaveURL(/\/configurations/);
  });

  test('view update removes banner', async ({ page }) => {
    await page.getByRole('link', { name: 'View updates' }).click();

    // Ensure banner is gone
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).not.toBeVisible();

    await expect(
      page.getByRole('heading', { name: 'App updates', exact: true, level: 1 })
    ).toBeVisible();
  });
});
