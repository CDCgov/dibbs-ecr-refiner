import { deleteAllConfigurations } from './db';
import { test, expect } from './fixtures/fixtures';

test.describe('Independent testing', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await configurationsPage.goto();
    await deleteAllConfigurations();
  });
  test.afterEach(async () => await deleteAllConfigurations());

  test('No active configurations', async ({ page, testingPage }) => {
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

  test('Only COVID-19 configuration in draft', async ({
    page,
    testingPage,
    api,
  }) => {
    await api.createConfiguration('COVID-19');
    await testingPage.goto();
    await testingPage.uploadTestFile();
    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).toBeVisible();
    await expect(page.getByText('Influenza')).toBeVisible();

    await expect(
      page.getByText(
        'No active configuration was detected for the following conditions. Please ensure there is an active configuration for each condition in order to receive a refined output for it.'
      )
    ).toBeVisible();
    await expect(page.getByText('COVID-19')).toBeVisible();

    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();
  });

  test('Only COVID-19 configuration is active', async ({
    page,
    testingPage,
    api,
  }) => {
    const config = await api.createConfiguration('COVID-19');
    await api.updateConfigurationStatus(config.id, 'active');

    await page.reload();

    await testingPage.goto();

    await testingPage.uploadTestFile();
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();
    await expect(page.getByText('Influenza')).toBeVisible();

    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).toBeVisible();
    await expect(page.getByText('COVID-19')).toBeVisible();

    await expect(
      page.getByRole('button', { name: 'Refine eCR' })
    ).toBeEnabled();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();

    await page.getByRole('button', { name: 'Refine eCR' }).click();
    await expect(
      page.getByRole('heading', { name: 'eCR refinement results' })
    ).toBeVisible();
    await expect(page.getByRole('option')).toHaveCount(1);
  });

  test('Both COVID-19 and Influenza configurations are active', async ({
    page,
    testingPage,
    api,
  }) => {
    const covid = await api.createConfiguration('COVID-19');
    await api.updateConfigurationStatus(covid.id, 'active');

    const flu = await api.createConfiguration('Influenza');
    await api.updateConfigurationStatus(flu.id, 'active');

    await page.reload();

    await testingPage.goto();

    await testingPage.uploadTestFile();
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();
    await expect(page.getByText('Influenza')).toBeVisible();
    await expect(page.getByText('COVID-19')).toBeVisible();

    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).not.toBeVisible();
    await expect(
      page.getByText(
        'No active configuration was detected for the following conditions. Please ensure there is an active configuration for each condition in order to receive a refined output for it.'
      )
    ).not.toBeVisible();

    await expect(
      page.getByRole('button', { name: 'Refine eCR' })
    ).toBeEnabled();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();

    await page.getByRole('button', { name: 'Refine eCR' }).click();
    await expect(
      page.getByRole('heading', { name: 'eCR refinement results' })
    ).toBeVisible();
    await expect(page.getByRole('option')).toHaveCount(2);
  });
});
