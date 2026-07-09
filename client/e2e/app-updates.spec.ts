import { test, expect } from './fixtures';

test.describe('App updates', () => {
  test.beforeEach(async ({ appUpdatesPage }) => {
    await appUpdatesPage.goto();
  });

  test('Page is accessible and has expected content', async ({
    makeAxeBuilder,
    page,
  }) => {
    await expect(
      page.getByRole('heading', { name: 'App updates', exact: true, level: 1 })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });
});
