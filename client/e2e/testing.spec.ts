import { Locator } from '@playwright/test';
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

  test('Only COVID-19 has been configured', async ({
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
    await expect(testingPage.getConditionCheckbox('COVID-19')).toBeVisible();
    await expect(
      testingPage.getConditionCheckbox('Influenza')
    ).not.toBeVisible();

    // select box should be available for COVID-19 configs
    await expect(
      testingPage.getConditionSelect('COVID-19').getByRole('option')
    ).toHaveCount(2);

    // no influenza select should be available
    await expect(testingPage.getConditionSelect('Influenza')).not.toBeVisible();

    // default option should be the active covid config
    await expect(
      testingPage.getConditionSelect('COVID-19').locator('option:checked')
    ).toHaveText('Version 1 (active)');

    // select the draft covid config
    await testingPage
      .getConditionSelect('COVID-19')
      .selectOption('Version 2 (draft)');

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

    const refineButton = page.getByRole('button', { name: 'Refine eCR' });

    await expect(refineButton).toBeEnabled();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();

    await refineButton.click();

    await expect(
      page.getByRole('heading', { name: 'eCR refinement results' })
    ).toBeVisible();
    await expect(page.getByLabel('CONDITION:').getByRole('option')).toHaveText([
      'COVID-19',
    ]);
  });

  test('Only Influenza is selected for refinement', async ({
    page,
    testingPage,
    api,
  }) => {
    await api.createConfiguration('COVID-19');
    await api.createConfiguration('Influenza');

    await testingPage.goto();

    await testingPage.uploadTestFile();
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();

    await testingPage.getConditionCheckbox('Influenza').click();

    await testingPage.runRefinement();
    await expect(page.getByLabel('CONDITION:').getByRole('option')).toHaveText([
      'COVID-19',
    ]);
  });

  test.skip('Refine eCR button is disabled when no selections are made', () => {});

  test('Both COVID-19 and Influenza configurations are selected for refinement', async ({
    page,
    testingPage,
    api,
  }) => {
    const covidActive = await api.createConfiguration('COVID-19');
    await api.updateConfigurationStatus(covidActive.id, 'active');

    // create covid draft
    const covidDraft = await api.createConfiguration('COVID-19');

    const fluDraft = await api.createConfiguration('Influenza');

    await testingPage.goto();

    await testingPage.uploadTestFile();
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();

    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).not.toBeVisible();

    // list indicates there were unmatched conditions
    await expect(page.getByRole('listitem')).not.toBeVisible();

    const covidCheckbox = testingPage.getConditionCheckbox('COVID-19');
    const covidSelect = page.getByLabel('COVID-19', { exact: true });

    const fluCheckbox = testingPage.getConditionCheckbox('Influenza');
    const fluSelect = page.getByLabel('Influenza', { exact: true });

    const getOptionValues = (select: Locator) =>
      select.evaluate((el: HTMLSelectElement) =>
        Array.from(el.options).map((o) => o.value)
      );

    await expect(covidCheckbox).toBeChecked();
    await expect(covidSelect).toBeVisible();
    await expect(covidSelect.getByRole('option')).toHaveText([
      'Version 2 (draft)',
      'Version 1 (active)',
    ]);

    const covidOptionValues = await getOptionValues(covidSelect);
    expect(covidOptionValues).toEqual([covidDraft.id, covidActive.id]);

    await expect(fluCheckbox).toBeChecked();
    await expect(fluSelect).toBeVisible();
    await expect(fluSelect.getByRole('option')).toHaveText([
      'Version 1 (draft)',
    ]);
    const fluOptionValues = await getOptionValues(fluSelect);
    expect(fluOptionValues).toEqual([fluDraft.id]);

    const refineButton = page.getByRole('button', { name: 'Refine eCR' });

    await expect(refineButton).toBeEnabled();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeEnabled();

    await refineButton.click();
    await expect(
      page.getByRole('heading', { name: 'eCR refinement results' })
    ).toBeVisible();

    await expect(page.getByLabel('CONDITION:').getByRole('option')).toHaveText([
      'COVID-19',
      'Influenza',
    ]);
  });
});
