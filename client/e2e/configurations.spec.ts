import { test, expect } from './fixtures';
import { deleteAllConfigurations } from './db';

test.describe('Configurations screen', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await deleteAllConfigurations();
    await configurationsPage.goto();
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

  test('Navigates to the active config when one exists', async ({
    api,
    page,
  }) => {
    // create and activate config
    const condition = 'Anotia';
    const config = await api.createConfiguration('Anotia');
    await api.updateConfigurationStatus(config.id, 'active');

    // create draft
    await api.createConfiguration('Anotia');

    await page.reload();

    await page.getByText(condition).click();

    await expect(page.getByText('Viewing: Version 1')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Go to draft' })).toBeVisible();
  });

  test('Navigates to the draft config when only a draft and inactive configs exist', async ({
    api,
    page,
  }) => {
    // create and activate config
    const condition = 'Anotia';
    const config = await api.createConfiguration('Anotia');
    await api.updateConfigurationStatus(config.id, 'active');

    // create draft
    await api.createConfiguration('Anotia');

    await api.updateConfigurationStatus(config.id, 'inactive');

    await page.reload();

    await page.getByText(condition).click();

    await expect(page.getByText('Editing: Version 2')).toBeVisible();
  });

  test('Navigates to the latest inactive config when only inactive configs exist', async ({
    api,
    page,
  }) => {
    // create and activate config
    const condition = 'Anotia';
    const config = await api.createConfiguration('Anotia');
    await api.updateConfigurationStatus(config.id, 'active');

    // create draft and then set inactive
    const draft = await api.createConfiguration('Anotia');
    await api.updateConfigurationStatus(draft.id, 'active');
    await api.updateConfigurationStatus(draft.id, 'inactive');

    await page.reload();

    await page.getByText(condition).click();

    await expect(page.getByText('Viewing: Version 2')).toBeVisible();
  });
});
