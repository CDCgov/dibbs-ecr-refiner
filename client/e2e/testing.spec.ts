import { deleteAllConfigurations } from './db';
import { test, expect } from './fixtures';

test.describe('Independent testing', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await configurationsPage.goto();
    await deleteAllConfigurations();
  });
  test.afterEach(async () => await deleteAllConfigurations());

  test('No available configurations', async ({ page, testingPage }) => {
    await testingPage.goto();
    await testingPage.uploadTestFile();
    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).toBeVisible();

    // no configs to select from
    await expect(page.getByRole('checkbox')).toHaveCount(0);
    await expect(page.getByRole('combobox')).toHaveCount(0);

    // only displays a list of conditions that were detected with no matching config
    await expect(
      page.getByRole('listitem').getByText('Influenza')
    ).toBeVisible();
    await expect(
      page.getByRole('listitem').getByText('COVID-19')
    ).toBeVisible();

    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();
    await testingPage.startOver();
    await expect(
      page.getByText('Want to refine your own eCR file?')
    ).toBeVisible();
    await expect(page.getByText('mon-mothma-two-conditions.zip')).toBeVisible();
  });

  test('Only COVID-19 configurations are available to select', async ({
    page,
    testingPage,
    api,
  }) => {
    // create config and activate it
    const covid = await api.createConfiguration('COVID-19');
    await api.updateConfigurationStatus(covid.id, 'active');

    // create a draft
    await api.createConfiguration('COVID-19');

    await testingPage.goto();
    await testingPage.uploadTestFile();

    // checkbox should be available for COVID-19 only
    await expect(
      page.getByLabel('Use COVID-19 configuration in refinement process')
    ).toBeVisible();
    await expect(
      page.getByLabel('Use Influenza configuration in refinement process')
    ).not.toBeVisible();

    // select box should be available for COVID-19 configs
    await expect(
      page.getByRole('combobox', { name: 'COVID-19' }).getByRole('option')
    ).toHaveCount(2);

    // no influenza select should be available
    await expect(
      page.getByRole('combobox', { name: 'Influenza' })
    ).not.toBeVisible();

    // default option should be the active covid config
    await expect(
      page.getByRole('combobox', { name: 'COVID-19' }).locator('option:checked')
    ).toHaveText('Version 1 (active)');

    // select the draft covid config
    await page.getByRole('combobox').selectOption('Version 2 (draft)');

    // check that warning displays for influenza
    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).toBeVisible();
    await expect(
      page.getByRole('listitem').getByText('Influenza')
    ).toBeVisible();
    await expect(
      page.getByRole('listitem').getByText('COVID-19')
    ).not.toBeVisible();

    await expect(
      page.getByRole('button', { name: 'Refine eCR' })
    ).toBeEnabled();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();
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
