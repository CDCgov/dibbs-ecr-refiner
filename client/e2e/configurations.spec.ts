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
    request,
    configurationsPage,
  }) => {
    const conditionsReq = await request.get('/api/v1/conditions/');
    expect(conditionsReq.ok()).toBeTruthy();
    const json = await conditionsReq.json();
    expect(json).toContainEqual(
      expect.objectContaining({
        display_name: 'Anotia',
      })
    );

    const anotia = (json as [{ id: string; display_name: string }]).find(
      (c) => c.display_name === 'Anotia'
    );
    expect(anotia).toBeTruthy();

    const configReq = await request.post('/api/v1/configurations/', {
      data: {
        condition_id: anotia?.id,
      },
    });
    expect(configReq.ok()).toBeTruthy();

    await page.reload();

    await expect(page.locator('table tbody tr')).toHaveCount(1);
    await expect(page.getByRole('cell')).toHaveCount(2);
    const cells = await page.getByRole('cell').all();
    await expect(cells[0]).toHaveText('Anotia');

    await configurationsPage.search('ano');
    await expect(cells[0]).toHaveText('Anotia');

    await configurationsPage.search('covid');
    await expect(cells[0]).toHaveText('No configurations available');
  });
});
