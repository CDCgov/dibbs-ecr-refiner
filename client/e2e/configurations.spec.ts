import { test, expect } from './fixtures/fixtures';
import { deleteAllConfigurations } from './db';

test.describe('Configurations screen', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await deleteAllConfigurations();
  });
  test.afterEach(async () => await deleteAllConfigurations());

  test('Check empty page state', async ({ page }) => {
    await expect(
      page.getByRole('heading', {
        name: 'Configurations',
        exact: true,
        level: 1,
      })
    ).toBeVisible();
    await expect(page.getByRole('searchbox')).not.toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Set up new configuration' })
    ).toBeEnabled();
    await expect(page.locator('table tbody tr')).toHaveCount(1);
    await expect(page.getByRole('cell')).toHaveText(
      'No configurations available'
    );
  });

  test('Check table with configurations', async ({
    page,
    api,
    configurationsPage,
  }) => {
    const config = await api.createConfiguration('Anotia');

    await page.reload();

    await expect(page.locator('table tbody tr')).toHaveCount(1);
    await expect(page.getByRole('cell')).toHaveCount(2);
    const cells = await page.getByRole('cell').all();
    await expect(cells[0]).toHaveText('Anotia');

    await configurationsPage.search('ano');
    await expect(cells[0]).toHaveText(config.name);

    await configurationsPage.search('covid');
    await expect(cells[0]).toHaveText('No configurations available');
  });
});
