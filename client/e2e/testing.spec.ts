import { deleteAllConfigurations } from './db';
import { test, expect } from './fixtures/fixtures';

test.describe('Independent testing', () => {
  test.beforeEach(async () => await deleteAllConfigurations());
  test.afterEach(async () => await deleteAllConfigurations());

  test('No active configurations', async ({
    page,
    testingPage,
    configurationsPage,
  }) => {
    await configurationsPage.goto();
    await testingPage.goto();
    await testingPage.uploadTestFile();
    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).toBeVisible();
    await expect(page.getByText('Influenza')).toBeVisible();
    await expect(page.getByText('COVID-19')).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();
    await testingPage.startOver();
    await expect(
      page.getByText('Want to refine your own eCR file?')
    ).toBeVisible();
    await expect(page.getByText('mon-mothma-two-conditions.zip')).toBeVisible();
  });
});
