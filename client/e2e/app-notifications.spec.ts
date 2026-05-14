import { test, expect } from './fixtures';
import { deleteAllConfigurations } from './db';
import { Page } from '@playwright/test';

async function waitForAcknowledgementRequest(page: Page) {
  return page.waitForRequest(
    (request) =>
      request.method() === 'PATCH' &&
      request.url().includes('/api/v1/notifications')
  );
}

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

  test('sends notification acknowledgement request when app update banner is dismissed', async ({
    page,
  }) => {
    const updateRequestPromise = waitForAcknowledgementRequest(page);

    await page.getByRole('button', { name: 'Dismiss notification' }).click();

    const updateRequest = await updateRequestPromise;
    const requestBody = updateRequest.postDataJSON();

    expect(requestBody.name).toBe('most_recent_app_update');
    expect(requestBody.date_acknowledged).toBeTruthy();
    expect(new Date(requestBody.date_acknowledged).toString()).not.toBe(
      'Invalid Date'
    );

    // Ensure banner is gone
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).not.toBeVisible();

    await expect(page).toHaveURL(/\/configurations/);
  });

  test('sends notification acknowledgement request when viewing app updates', async ({
    page,
  }) => {
    const updateRequestPromise = waitForAcknowledgementRequest(page);

    await page.getByRole('link', { name: 'View updates' }).click();

    const updateRequest = await updateRequestPromise;
    const requestBody = updateRequest.postDataJSON();

    expect(requestBody.name).toBe('most_recent_app_update');
    expect(requestBody.date_acknowledged).toBeTruthy();
    expect(new Date(requestBody.date_acknowledged).toString()).not.toBe(
      'Invalid Date'
    );

    // Ensure banner is gone
    await expect(
      page.getByText('There are new updates to eCR Refiner.')
    ).not.toBeVisible();

    await expect(
      page.getByRole('heading', { name: 'App updates', exact: true, level: 1 })
    ).toBeVisible();
  });
});
