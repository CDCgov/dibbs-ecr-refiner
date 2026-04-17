import { test, expect } from './fixtures';
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

    const conditionCell = cells[0];
    await expect(conditionCell).toHaveText('Anotia');

    await configurationsPage.search('ano');
    await expect(conditionCell).toHaveText(config.name);

    await configurationsPage.search('covid');
    await expect(conditionCell).toHaveText('No configurations available');

    await configurationsPage.clearSearch();

    await conditionCell.click();
    await expect(
      page.getByRole('heading', { name: config.name, level: 1 })
    ).toBeVisible();
  });
});
