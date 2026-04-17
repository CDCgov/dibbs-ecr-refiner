import { test, expect } from './fixtures/fixtures';

test.describe('App updates', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await configurationsPage.goto();
  });
  test('Page is accessible and has expected content', async ({
    makeAxeBuilder,
    page,
  }) => {
    await page.getByRole('button', { name: 'Open settings menu' }).click();
    const appUpdatesMenuItem = page.getByRole('menuitem', {
      name: 'App updates',
    });
    await expect(appUpdatesMenuItem).toBeVisible();
    await appUpdatesMenuItem.click();
    await expect(
      page.getByRole('heading', { name: 'App updates', exact: true, level: 1 })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });
});
