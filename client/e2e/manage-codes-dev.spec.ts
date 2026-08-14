/**
 * 👉 NOTE: This file is temporary. Once the `/manage-codes/view` route makes it into the
 * configuration flow this file's name will be changed or the code in the file
 * will be moved into the `configuration.spec.ts` file
 */

import { test, expect } from './fixtures';
import { clearDb } from './db';
import { Page } from '@playwright/test';
import { ConfigurationPage } from './pages/ConfigurationPage';

// This value represents the maximum number of table rows that load per page.
// Refer to: `refiner/app/api/v1/configurations/codes/codes.py` (`get_codes()` route)
const MAX_PAGE_SIZE = 100;

/**
 * Temporary helper to navigate to the /view route
 */
async function goToManageCodesDevPage(
  page: Page,
  configurationPage: ConfigurationPage
) {
  await configurationPage.goToManageCodesTab();
  const currentUrl = page.url();
  const newUrl = currentUrl + '/view';
  await page.goto(newUrl);
}

test.describe('Codes management - filters', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearDb();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
  });

  test('Page loads with no filters selected', async ({
    page,
    configurationsPage,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
    await expect(
      page.getByRole('heading', { name: 'Manage codes', level: 2 })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(page.getByText('Filter by:')).toBeVisible();

    const codeSystemFilterButton = page.getByRole('button', {
      name: 'Code system',
    });
    await expect(codeSystemFilterButton).toBeVisible();
    await codeSystemFilterButton.click();
    const codeSystemOptions = page
      .getByRole('listbox', { name: 'Code system' })
      .getByRole('option');

    await expect(page.getByRole('listbox')).toBeVisible();

    // all 6 systems should be present + clear selection
    await expect(codeSystemOptions).toHaveCount(7);

    await page.keyboard.press('Escape');
    const sourcesFilterButton = page.getByRole('button', { name: 'Source' });
    await expect(sourcesFilterButton).toBeVisible();
    await sourcesFilterButton.click();
    await expect(page.getByRole('listbox')).toBeVisible();
    const sourcesOptions = page
      .getByRole('listbox', { name: 'Source' })
      .getByRole('option');

    // only the condition + clear selection
    await expect(sourcesOptions).toHaveCount(2);

    await page.keyboard.press('Escape');
    const statusFilterButton = page.getByRole('button', { name: 'Status' });
    await expect(statusFilterButton).toBeVisible();
    await statusFilterButton.click();
    await expect(page.getByRole('listbox')).toBeVisible();
    const statusOptions = page
      .getByRole('listbox', { name: 'Status' })
      .getByRole('option');

    // Both included and excluded + clear selection
    await expect(statusOptions).toHaveCount(3);
    await page.keyboard.press('Escape');

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('User can filter on code system', async ({
    page,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
    await expect(
      page.getByRole('heading', { name: 'Manage codes', level: 2 })
    ).toBeVisible();

    const codeSystemFilterButton = page.getByTestId('code-system-button');
    const codeSystemOptions = page.getByTestId('code-system-options');

    await expect(codeSystemFilterButton).toBeVisible();
    await codeSystemFilterButton.click();

    const loincOption = codeSystemOptions.getByRole('option', {
      name: 'LOINC',
      exact: false,
    });
    const cvxOption = codeSystemOptions.getByRole('option', {
      name: 'CVX',
      exact: false,
    });

    await loincOption.click();
    await page.keyboard.press('Escape');
    await expect(codeSystemFilterButton).toContainText('1 selected');

    await codeSystemFilterButton.click();
    await expect(cvxOption).toBeVisible();
    await cvxOption.click();
    await page.keyboard.press('Escape');
    await expect(codeSystemFilterButton).toContainText('2 selected');

    await codeSystemFilterButton.click();
    const clearButton = codeSystemOptions.getByRole('option', {
      name: 'Clear selection',
    });
    await expect(clearButton).toBeVisible();
    await clearButton.click();
    await page.keyboard.press('Escape');
    await expect(codeSystemFilterButton).toContainText('Code system');
  });

  test('User can filter on source', async ({
    page,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
    await expect(
      page.getByRole('heading', { name: 'Manage codes', level: 2 })
    ).toBeVisible();

    await test.step('Add Acanthamoeba code set', async () => {
      await page.getByRole('button', { name: '1 Condition code sets' }).click();
      await page
        .getByRole('searchbox', { name: 'Search by condition name' })
        .fill('acanth');
      await page
        .getByRole('listitem')
        .filter({ hasText: 'Acanthamoeba' })
        .hover();
      await page.getByLabel('Add Acanthamoeba').click();
      await page.getByRole('button', { name: 'Close drawer' }).click();
    });

    await test.step('Check source filter', async () => {
      const sourceFilterButton = page.getByTestId('source-button');
      const sourceOptions = page.getByTestId('source-options');

      await expect(sourceFilterButton).toBeVisible();
      await sourceFilterButton.click();

      // should show added code set as an option
      const acanthamoebaOption = sourceOptions.getByRole('option', {
        name: 'Acanthamoeba',
        exact: false,
      });

      const anotiaOption = sourceOptions.getByRole('option', {
        name: 'Anotia',
        exact: false,
      });

      await expect(acanthamoebaOption).toBeVisible();
      await expect(anotiaOption).toBeVisible();

      await acanthamoebaOption.click();
      await page.keyboard.press('Escape');
      await expect(sourceFilterButton).toContainText('1 selected');
    });
  });

  test('User can filter on status', async ({
    page,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
    await expect(
      page.getByRole('heading', { name: 'Manage codes', level: 2 })
    ).toBeVisible();

    const sourceFilterButton = page.getByTestId('status-button');
    const sourceOptions = page.getByTestId('status-options');

    await expect(sourceFilterButton).toBeVisible();
    await sourceFilterButton.click();

    const includedOption = sourceOptions.getByRole('option', {
      name: 'Included',
      exact: false,
    });

    const excludedOption = sourceOptions.getByRole('option', {
      name: 'Excluded',
      exact: false,
    });

    await expect(includedOption).toBeVisible();
    await expect(excludedOption).toBeVisible();

    await excludedOption.click();
    await page.keyboard.press('Escape');
    await expect(sourceFilterButton).toContainText('1 selected');
  });

  test('Deleting all custom codes removes it as a filter option', async ({
    page,
    configurationPage,
    api,
  }) => {
    const sourceFilterButton = page.getByTestId('source-button');
    const sourceOptions = page.getByTestId('source-options');
    const customCodeOption = sourceOptions.getByRole('option', {
      name: 'Custom Code',
      exact: false,
    });

    await test.step('Set up configuration', async () => {
      const condition = 'Anotia';
      const config = await api.createConfiguration(condition);
      const systems = await api.getSystems();
      await api.uploadCustomCodeCsv(config.id, [
        {
          code: '123-4',
          display: 'mock custom code',
          system_id: systems[0].id,
        },
      ]);
    });

    await test.step('Navigate to management page', async () => {
      await page.reload();
      await expect(
        page.getByRole('heading', { name: 'Configurations', level: 1 })
      ).toBeVisible();
      await page.getByRole('link', { name: 'Anotia' }).click();
      await expect(
        page.getByRole('heading', { name: 'Customize eICR sections' })
      ).toBeVisible();
      await goToManageCodesDevPage(page, configurationPage);
    });

    await test.step('Select custom code in source filter', async () => {
      await expect(page.locator('table tr').nth(1)).toContainText('123-4');

      await expect(sourceFilterButton).toBeVisible();
      await sourceFilterButton.click();

      await customCodeOption.click();
      await page.keyboard.press('Escape');
      await expect(sourceFilterButton).toHaveText('1 selected');
    });

    await test.step('Delete custom code and check that filter updated', async () => {
      const customCodeRow = page.locator('table tr').nth(1);
      await expect(customCodeRow).toBeVisible();
      await customCodeRow.getByRole('button', { name: 'Delete' }).click();
      await expect(sourceFilterButton).toHaveText('Source');
      await sourceFilterButton.click();
      await expect(customCodeOption).not.toBeVisible();
    });
  });
});

test.describe('Codes management - data loading and interactions', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearDb();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
  });

  test('Unaltered, initial page layout check', async ({
    page,
    configurationsPage,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
    await expect(
      page.getByRole('heading', { name: 'Manage codes', level: 2 })
    ).toBeVisible();

    await expect(page.getByTestId('codes-included-display')).toHaveText(
      '2 of 2 codes included'
    );
    await expect(page.getByText('0 excluded')).toBeVisible();
    await expect(page.getByText('0 custom')).toBeVisible();
    await expect(page.getByText('1 condition code sets')).toBeVisible();
    await expect(page.getByText("You've reached the end")).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Custom codes appear at the top of the table', async ({
    page,
    configurationPage,
    api,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    const config = await api.createConfiguration(condition);
    const systems = await api.getSystems();
    await api.uploadCustomCodeCsv(config.id, [
      {
        code: '123-4',
        display: 'test code 1',
        system_id: systems[0].id,
      },
      {
        code: '432-1',
        display: 'test code 2',
        system_id: systems[1].id,
      },
    ]);
    await page.reload();
    await expect(
      page.getByRole('heading', { name: 'Configurations', level: 1 })
    ).toBeVisible();
    await page.getByRole('link', { name: 'Anotia' }).click();
    await expect(
      page.getByRole('heading', { name: 'Customize eICR sections' })
    ).toBeVisible();
    await goToManageCodesDevPage(page, configurationPage);

    // check top two rows
    await expect(page.locator('table tr').nth(1)).toContainText('123-4');
    await expect(page.locator('table tr').nth(2)).toContainText('432-1');

    // check stats
    await expect(page.getByTestId('codes-included-display')).toHaveText(
      '4 of 4 codes included'
    );
    await expect(page.getByText('0 excluded')).toBeVisible();
    await expect(page.getByText('2 custom')).toBeVisible();
    await expect(page.getByText('1 condition code sets')).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Custom codes cannot be excluded', async ({
    api,
    page,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    const config = await api.createConfiguration(condition);
    const systems = await api.getSystems();
    await api.uploadCustomCodeCsv(config.id, [
      {
        code: 'test-code-1',
        display: 'My test code',
        system_id: systems[0].id,
      },
    ]);

    await page.reload();
    await expect(
      page.getByRole('heading', { name: 'Configurations', level: 1 })
    ).toBeVisible();
    await page.getByRole('link', { name: 'Anotia' }).click();
    await expect(
      page.getByRole('heading', { name: 'Customize eICR sections' })
    ).toBeVisible();
    await goToManageCodesDevPage(page, configurationPage);

    const row = page.locator('table tr').filter({
      has: page.locator('td', {
        hasText: 'test-code-1',
      }),
    });

    const switchCell = row.locator('td').last();
    await expect(switchCell).toHaveText('Included');
    await expect(switchCell.getByRole('switch')).toBeDisabled();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Individual codes can be toggled to be included/excluded', async ({
    page,
    configurationsPage,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);

    // get the row by description text
    const row = page.locator('table tr').filter({
      has: page.locator('td', {
        hasText: 'Congenital absence of (ear) auricle',
      }),
    });

    const switchCell = row.locator('td').last();

    await expect(switchCell).toHaveText('Included');
    const includeExcludeSwitch = switchCell.getByRole('switch');
    await includeExcludeSwitch.click();
    await expect(switchCell).toHaveText('Excluded');

    await test.step('Check stats bar', async () => {
      await expect(page.getByTestId('codes-included-display')).toHaveText(
        '1 of 2 codes included'
      );
      await expect(page.getByText('1 excluded')).toBeVisible();
    });

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Individual custom codes can be added, edited, and deleted', async ({
    page,
    configurationsPage,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);

    const code = '123-4';
    const system = 'CVX';
    const name = 'code name';

    await test.step('Add custom code', async () => {
      await page.getByRole('button', { name: 'Add custom code' }).click();
      await page.getByRole('button', { name: 'Add a single code' }).click();

      const modal = page.getByRole('dialog');

      await modal.getByLabel('Code', { exact: true }).fill(code);
      await modal
        .getByLabel('Code system', { exact: true })
        .selectOption({ label: system });
      await modal.getByLabel('Display name').fill(name);
      await modal.getByRole('button', { name: 'Add custom code' }).click();
      await expect(
        page.getByRole('heading', { name: 'Manage codes', level: 2 })
      ).toBeVisible();
      await page.getByText('Custom code added').click();
    });

    await test.step('Validate added code', async () => {
      const row = page.locator('table tr').filter({
        has: page.locator('td', {
          hasText: code,
        }),
      });
      const codeNumberCell = row.locator('td').nth(1);
      const systemCell = row.locator('td').nth(2);
      const descriptionCell = row.locator('td').nth(3);
      const sourceCell = row.locator('td').nth(4);

      await expect(codeNumberCell).toHaveText(code);
      await expect(systemCell).toHaveText(system);
      await expect(descriptionCell).toHaveText(name);

      await expect(sourceCell).toContainText('Custom code');
      await expect(
        sourceCell.getByRole('button', { name: 'Edit' })
      ).toBeVisible();
      await expect(
        sourceCell.getByRole('button', { name: 'Delete' })
      ).toBeVisible();
    });

    await test.step('Edit custom code', async () => {
      const row = page.locator('table tr').filter({
        has: page.locator('td', {
          hasText: code,
        }),
      });
      await row.getByRole('button', { name: 'Edit' }).click();

      await expect(
        page.getByRole('heading', { name: 'Edit custom code', level: 2 })
      ).toBeVisible();
      await expect(page.getByLabel('Code', { exact: true })).toHaveValue(code);
      await expect(
        page.getByLabel('Code system').locator('option:checked')
      ).toHaveText(system);
      await expect(page.getByLabel('Display name')).toHaveValue(name);

      await page.getByLabel('Code', { exact: true }).fill('new code');
      await page.getByLabel('Display name').focus();
      await expect(page.getByRole('button', { name: 'Update' })).toBeEnabled();
      await page.getByRole('button', { name: 'Update' }).click();
      await expect(
        page.getByRole('heading', { name: 'Manage codes', level: 2 })
      ).toBeVisible();

      await expect(page.getByText('123-4')).toBeVisible();
    });
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Condition code sets can be added and deleted', async ({
    page,
    configurationsPage,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);

    await test.step('Add Acanthamoeba code set', async () => {
      await page.getByRole('button', { name: '1 Condition code sets' }).click();
      await page
        .getByRole('searchbox', { name: 'Search by condition name' })
        .fill('acanth');
      await page
        .getByRole('listitem')
        .filter({ hasText: 'Acanthamoeba' })
        .hover();
      await page.getByLabel('Add Acanthamoeba').click();
      await page.getByRole('button', { name: 'Close drawer' }).click();
    });

    await test.step('Check page state after addition', async () => {
      await expect(page.getByTestId('codes-included-display')).toHaveText(
        '940 of 940 codes included'
      );
      await expect(page.getByText('2 condition code sets')).toBeVisible();
      await expect(page.locator('table tr')).toHaveCount(MAX_PAGE_SIZE + 1); // page size + header row
    });

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await test.step('Remove Acanthamoeba code set', async () => {
      await page.getByRole('button', { name: '2 Condition code sets' }).click();
      await page
        .getByRole('searchbox', { name: 'Search by condition name' })
        .fill('acanth');
      await page
        .getByRole('listitem')
        .filter({ hasText: 'Acanthamoeba' })
        .hover();
      await page.getByLabel('Remove Acanthamoeba').click();
      await page.getByRole('button', { name: 'Close drawer' }).click();
    });

    await test.step('Check page state after removal', async () => {
      await expect(page.getByTestId('codes-included-display')).toHaveText(
        '2 of 2 codes included'
      );
      await expect(page.getByText('1 condition code sets')).toBeVisible();
      await expect(page.locator('table tr')).toHaveCount(3); // two Anotia codes + header row
    });

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('More codes load into view as user scrolls down', async ({
    page,
    configurationsPage,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);

    await test.step('Add code set', async () => {
      await page.getByRole('button', { name: '1 Condition code sets' }).click();
      await page
        .getByRole('searchbox', { name: 'Search by condition name' })
        .fill('acanth');
      await page
        .getByRole('listitem')
        .filter({ hasText: 'Acanthamoeba' })
        .hover();
      await page.getByLabel('Add Acanthamoeba').click();
      await page.getByRole('button', { name: 'Close drawer' }).click();
    });

    await expect(page.locator('table tr')).toHaveCount(MAX_PAGE_SIZE + 1); // page size + header row

    await page.locator('table tr').last().scrollIntoViewIfNeeded();

    // Scrolling down should add `MAX_PAGE_SIZE` to the table
    const expectedRowCountAfterLoad = 2 * MAX_PAGE_SIZE + 1;
    await expect(page.locator('table tr')).toHaveCount(
      expectedRowCountAfterLoad
    );

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });
});
