import { Locator } from '@playwright/test';
import { clearDb } from './db';
import { test, expect } from './fixtures';

test.describe('Simulate testing', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await configurationsPage.goto();
    await clearDb();
  });
  test.afterEach(async () => await clearDb());

  test('No available configurations', async ({
    page,
    simulatorPage,
    makeAxeBuilder,
  }) => {
    await simulatorPage.goto();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await simulatorPage.uploadTestFile();
    await expect(
      page.getByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).toBeVisible();

    // no configs to select from
    await expect(page.getByRole('checkbox')).toHaveCount(0);
    await expect(page.getByRole('combobox')).toHaveCount(0);

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

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

    await simulatorPage.startOver();

    await expect(
      page.getByText('Want to refine your own eCR file?')
    ).toBeVisible();
    await expect(page.getByText('mon-mothma-two-conditions.zip')).toBeVisible();
  });

  test('Should be able to handle a reasonable amount of configuration options', async ({
    simulatorPage,
    api,
    makeAxeBuilder,
  }) => {
    for (let i = 0; i < 20; i++) {
      /*
      Note that activating a config automatically de-activates the previous one.
      */
      const covid = await api.createConfiguration('COVID-19');
      await api.updateConfigurationStatus(covid.id, 'active');
    }

    await api.createConfiguration('COVID-19');

    await simulatorPage.goto();
    await simulatorPage.uploadTestFile();

    // 19 inactive, 1 active, and 1 draft
    await expect(
      simulatorPage.getConditionSelect('COVID-19').getByRole('option')
    ).toHaveCount(21);

    await expect(
      simulatorPage.getConditionSelect('COVID-19').locator('option:checked')
    ).toHaveText('Version 20 (active)');

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Only COVID-19 has been configured', async ({
    page,
    simulatorPage,
    api,
    makeAxeBuilder,
  }) => {
    // create config and activate it
    const covid = await api.createConfiguration('COVID-19');
    await api.updateConfigurationStatus(covid.id, 'active');

    // create a draft
    await api.createConfiguration('COVID-19');

    await simulatorPage.goto();
    await simulatorPage.uploadTestFile();

    // checkbox should be available for COVID-19 only
    await expect(simulatorPage.getConditionCheckbox('COVID-19')).toBeVisible();
    await expect(
      simulatorPage.getConditionCheckbox('Influenza')
    ).not.toBeVisible();

    // select box should be available for COVID-19 configs
    await expect(
      simulatorPage.getConditionSelect('COVID-19').getByRole('option')
    ).toHaveCount(2);

    // no influenza select should be available
    await expect(
      simulatorPage.getConditionSelect('Influenza')
    ).not.toBeVisible();

    // default option should be the active covid config
    await expect(
      simulatorPage.getConditionSelect('COVID-19').locator('option:checked')
    ).toHaveText('Version 1 (active)');

    // select the draft covid config
    await simulatorPage
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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Only Influenza is selected for refinement', async ({
    page,
    simulatorPage,
    api,
    makeAxeBuilder,
  }) => {
    await api.createConfiguration('COVID-19');
    await api.createConfiguration('Influenza');

    await simulatorPage.goto();

    await simulatorPage.uploadTestFile();
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();

    await simulatorPage.getConditionCheckbox('Influenza').click();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await simulatorPage.runRefinement();
    await expect(page.getByLabel('CONDITION:').getByRole('option')).toHaveText([
      'COVID-19',
    ]);

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Refine eCR button is disabled when no selections are made', async ({
    page,
    simulatorPage,
    api,
    makeAxeBuilder,
  }) => {
    await api.createConfiguration('COVID-19');
    await api.createConfiguration('Influenza');

    await simulatorPage.goto();

    await simulatorPage.uploadTestFile();

    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();

    const checkboxes = page.getByRole('checkbox');
    const count = await checkboxes.count();
    expect(count).toBe(2);

    for (let i = 0; i < count; i++) {
      const checkbox = checkboxes.nth(i);
      await checkbox.uncheck();
    }

    const refineButton = page.getByRole('button', { name: 'Refine eCR' });
    await expect(refineButton).toBeDisabled();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await checkboxes.nth(0).check();
    await expect(refineButton).toBeEnabled();
  });

  test('Both COVID-19 and Influenza configurations are selected for refinement', async ({
    page,
    simulatorPage,
    api,
    makeAxeBuilder,
  }) => {
    const covidActive = await api.createConfiguration('COVID-19');
    await api.updateConfigurationStatus(covidActive.id, 'active');

    // create covid draft
    const covidDraft = await api.createConfiguration('COVID-19');

    const fluDraft = await api.createConfiguration('Influenza');

    await simulatorPage.goto();

    await simulatorPage.uploadTestFile();
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

    const covidCheckbox = simulatorPage.getConditionCheckbox('COVID-19');
    const covidSelect = page.getByLabel('COVID-19', { exact: true });

    const fluCheckbox = simulatorPage.getConditionCheckbox('Influenza');
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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await refineButton.click();
    await expect(
      page.getByRole('heading', { name: 'eCR refinement results' })
    ).toBeVisible();

    await expect(page.getByLabel('CONDITION:').getByRole('option')).toHaveText([
      'COVID-19',
      'Influenza',
    ]);

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });
});
