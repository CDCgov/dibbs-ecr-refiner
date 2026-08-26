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

test.describe('Codes management - custom code interactions', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearDb();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
  });

  test('Custom code options are only available in the control panel when custom codes are selected', async ({
    page,
    configurationPage,
    configurationsPage,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);

    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    const selectAllCheckbox = table.getByRole('checkbox', {
      name: 'Include all codes in bulk operation',
    });
    await selectAllCheckbox.click();
    await expect(selectAllCheckbox).toBeChecked();

    const controlPanel = page.getByTestId('control-panel');
    await expect(controlPanel).toBeVisible();
    await expect(
      controlPanel.getByRole('button', { name: 'Include' })
    ).toBeVisible();
    await expect(
      controlPanel.getByRole('button', { name: 'Exclude' })
    ).toBeVisible();
    await expect(
      controlPanel.getByRole('button', { name: 'More options' })
    ).not.toBeVisible();
  });

  test('Including a custom code has no effect', async ({
    api,
    page,
    configurationPage,
  }) => {
    await test.step('Set up configuration', async () => {
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
    });

    await test.step('Navigate to page', async () => {
      await page.reload();
      await expect(
        page.getByRole('heading', { name: 'Configurations', level: 1 })
      ).toBeVisible();
      await page.getByRole('link', { name: 'Anotia' }).click();
      await expect(
        page.getByRole('heading', { name: 'Customize eICR sections' })
      ).toBeVisible();
      await goToManageCodesDevPage(page, configurationPage);
      await expect(
        page.getByRole('heading', { name: 'Manage codes', level: 2 })
      ).toBeVisible();
    });

    await test.step('Set all codes to be Included', async () => {
      const table = page.getByRole('table');
      await expect(table).toBeVisible();

      const selectAllCheckbox = table.getByRole('checkbox', {
        name: 'Include all codes in bulk operation',
      });
      await selectAllCheckbox.click();
      await expect(selectAllCheckbox).toBeChecked();

      const controlPanel = page.getByTestId('control-panel');
      await expect(controlPanel).toBeVisible();
      await expect(controlPanel).toContainText('3 selected');
      await controlPanel.getByRole('button', { name: 'Include' }).click();
      await expect(controlPanel).not.toBeVisible();

      const statusCells = table.locator('tbody tr td:last-child');
      for (const cell of await statusCells.all()) {
        await expect(cell).not.toContainText('Excluded');
      }
    });
  });

  test('Custom codes can be deleted in bulk', async ({
    api,
    page,
    configurationPage,
  }) => {
    await test.step('Set up configuration', async () => {
      const condition = 'Anotia';
      const config = await api.createConfiguration(condition);
      const systems = await api.getSystems();
      await api.uploadCustomCodeCsv(config.id, [
        {
          code: 'test-code-1',
          display: 'My test code',
          system_id: systems[0].id,
        },
        {
          code: 'test-code-2',
          display: 'My secondary test code',
          system_id: systems[1].id,
        },
      ]);
    });

    await test.step('Navigate to page', async () => {
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

    await test.step('Bulk delete custom codes', async () => {
      const table = page.getByRole('table');
      await expect(table).toBeVisible();

      const selectAllCheckbox = table.getByRole('checkbox', {
        name: 'Include all codes in bulk operation',
      });
      await selectAllCheckbox.click();
      await expect(selectAllCheckbox).toBeChecked();

      const controlPanel = page.getByTestId('control-panel');
      await expect(controlPanel).toBeVisible();
      await expect(controlPanel).toContainText('4 selected');
      await controlPanel.getByRole('button', { name: 'More options' }).click();

      const customCodeDeletionButton = page.getByText('Delete 2 custom codes');
      await expect(customCodeDeletionButton).toBeVisible();
      await customCodeDeletionButton.click();

      await expect(
        page.getByText('2 custom codes will be deleted')
      ).toBeVisible();
      const deleteButton = page.getByRole('button', { name: 'Delete 2 codes' });
      await expect(deleteButton).toBeVisible();
      await deleteButton.click();
      await expect(controlPanel).not.toBeVisible();

      const sourceCells = table.locator('tbody tr td:nth-last-child(2)');
      for (const cell of await sourceCells.all()) {
        await expect(cell).not.toContainText('Custom code');
      }
    });
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

    const row = page.getByRole('table').getByRole('row').nth(1);
    const statusCell = row.getByRole('cell').last();

    await expect(statusCell).toHaveText('Included');

    const checkbox = row.getByRole('cell').first();
    await checkbox.click();

    const controlPanel = page.getByTestId('control-panel');
    await expect(controlPanel).toBeVisible();
    await controlPanel.getByRole('button', { name: 'Exclude' }).click();

    const modal = page.getByRole('dialog');

    await expect(
      modal.getByRole('heading', { name: 'Exclude codes', level: 2 })
    ).toBeVisible();
    await expect(
      modal.getByText('None of the selected codes can be excluded.')
    ).toBeVisible();
    await expect(modal.getByRole('button')).toHaveCount(2); // Only 'cancel' and 'X' buttons available
    await modal.getByRole('button', { name: 'Cancel' }).click();

    await expect(controlPanel).toBeVisible();

    // should be no change
    await expect(statusCell).toHaveText('Included');
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Custom codes can be imported using the CSV upload screen', async ({
    page,
    configurationPage,
    configurationsPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);

    await expect(page.getByRole('table')).toBeVisible();
    const addCustomCodesButton = page.getByRole('button', {
      name: 'Add custom code',
    });
    await expect(addCustomCodesButton).toBeVisible();

    await addCustomCodesButton.click();

    const importCsvButton = page.getByRole('button', {
      name: 'Import codes from CSV',
    });
    await expect(importCsvButton).toBeVisible();

    await importCsvButton.click();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(page.getByRole('table')).not.toBeVisible();

    await expect(
      page.getByRole('heading', {
        name: 'Import from CSV',
        exact: true,
        level: 2,
      })
    ).toBeVisible();

    const csvWithBadHeaders = `cod,code_system,display_name
      6789,ICD-10,ICD-10 Example
      `;

    await page.locator('input[type="file"]').setInputFiles({
      name: 'bad_headers.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvWithBadHeaders),
    });

    await expect(
      page.getByRole('alert').filter({
        hasText: /^CSV must contain headers: code, code_system, display_name/,
      })
    ).toBeVisible();

    const csvWithBadSystem = `code,code_system,display_name
      6789,ICD-1,ICD-10 Example`;

    await page.locator('input[type="file"]').setInputFiles({
      name: 'bad_system.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvWithBadSystem),
    });

    await expect(page.getByText('Row 2', { exact: false })).toBeVisible();
    await expect(
      page.getByText(
        'Invalid system: ICD-1. [code_system] must be one of [SNOMED, LOINC, ICD-10, RxNorm, CVX, Other]'
      )
    ).toBeVisible();
    await page.getByRole('button', { name: '← Back' }).click();

    await expect(addCustomCodesButton).toBeVisible();
    await addCustomCodesButton.click();
    await expect(importCsvButton).toBeVisible();
    await importCsvButton.click();

    const downloadPath =
      await configurationPage.downloadCustomCodeCsvTemplate();
    await configurationPage.uploadCustomCodeCsv(downloadPath);
    const saveAllButton = page.getByRole('button', {
      name: 'Confirm & save codes',
    });
    const deleteAllButton = page.getByRole('button', {
      name: 'Undo & delete codes',
    });

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(saveAllButton).toBeVisible();
    await expect(deleteAllButton).toBeVisible();

    await expect(
      page.getByText('Other Example', { exact: true })
    ).toBeVisible();
    await page.getByRole('searchbox', { name: 'Search codes' }).fill('oth');
    const editButton = page.getByRole('button', {
      name: 'Edit',
      exact: true,
    });
    const deleteButton = page.getByRole('button', {
      name: 'Delete',
      exact: true,
    });
    await expect(editButton).toBeVisible();
    await expect(deleteButton).toBeVisible();

    await editButton.click();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(
      page.getByRole('heading', { name: `Edit 1111111-other`, level: 2 })
    ).toBeVisible();
    const testCode = 'test code ~';
    await page.getByLabel('Code', { exact: true }).fill(testCode);
    await page.getByLabel('Code system').selectOption({ label: 'CVX' });
    await page.getByLabel('Display name').fill('test display_name');
    await page.getByRole('button', { name: 'Save changes' }).click();
    await page
      .getByRole('searchbox', { name: 'Search codes' })
      .fill('test display_name');

    await editButton.click();
    await expect(
      page.getByRole('heading', { name: `Edit ${testCode}`, level: 2 })
    ).toBeVisible();
    await page.getByRole('button', { name: 'Close this window' }).click();
    await expect(
      page.getByText('Other Example', { exact: true })
    ).not.toBeVisible();
    await page.getByRole('searchbox', { name: 'Search codes' }).clear();

    const rows = page.locator('table tbody tr');
    await page.getByRole('searchbox', { name: 'Search codes' }).fill('test');

    const firstRow = rows.first();
    // first row should have the most recent updated values
    await expect(firstRow.getByText(testCode)).toBeVisible();
    await expect(firstRow.getByText('test display_name')).toBeVisible();
    await expect(firstRow.getByText('CVX')).toBeVisible();

    await firstRow.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByText(testCode)).not.toBeVisible();
    await page.getByRole('searchbox', { name: 'Search codes' }).clear();

    expect(await rows.all()).toHaveLength(5); // 6 code systems minus one

    await page.getByRole('button', { name: 'Confirm & save codes' }).click();
    await expect(
      page.getByRole('heading', {
        name: 'Confirm & save codes?',
        exact: true,
        level: 2,
      })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await page.getByRole('button', { name: 'Yes, save codes' }).click();

    const savedCodeTableRows = page.locator('table tbody tr');
    await expect(savedCodeTableRows.getByText('ICD-10 Example')).toBeVisible();
    await expect(savedCodeTableRows.getByText('LOINC Example')).toBeVisible();

    // make sure we're returned to the starting screen
    await expect(page.getByTestId('codes-included-display')).toBeVisible();
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

      await expect(
        page.getByRole('cell', { name: 'new code', exact: true })
      ).toBeVisible();
    });
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });
});

test.describe('Codes management - code set interactions', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearDb();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
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
});

test.describe('Codes management - code interactions', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearDb();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
  });

  test('Code set codes can be included and excluded', async ({
    page,
    configurationsPage,
    configurationPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);

    const row = page.getByRole('table').getByRole('row').nth(1);
    const checkbox = row.getByRole('cell').first().getByRole('checkbox');
    const statusCell = row.getByRole('cell').last();

    await expect(checkbox).toBeVisible();
    await expect(checkbox).toBeEnabled();
    await expect(statusCell).toContainText('Included');

    await checkbox.click();

    const controlPanel = page.getByTestId('control-panel');
    await expect(controlPanel).toBeVisible();
    await controlPanel.getByRole('button', { name: 'Exclude' }).click();

    await test.step('Check stats bar after excluding one code', async () => {
      await expect(page.getByTestId('codes-included-display')).toHaveText(
        '1 of 2 codes included'
      );
      await expect(page.getByText('1 excluded')).toBeVisible();
      await expect(controlPanel).not.toBeVisible();
    });

    const selectAllCheckbox = page.getByRole('table').getByRole('checkbox', {
      name: 'Include all codes in bulk operation',
    });
    await selectAllCheckbox.click();
    await expect(selectAllCheckbox).toBeChecked();
    await expect(controlPanel).toBeVisible();

    await controlPanel.getByRole('button', { name: 'Include' }).click();
    await expect(controlPanel).not.toBeVisible();

    await test.step('Check stats bar after including all', async () => {
      await expect(page.getByTestId('codes-included-display')).toHaveText(
        '2 of 2 codes included'
      );
      await expect(page.getByText('0 excluded')).toBeVisible();
      await expect(controlPanel).not.toBeVisible();
    });

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });
});

test.describe('Codes management - search', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearDb();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
  });

  test('User entering search text will filter the table', async ({
    api,
    page,
    configurationPage,
  }) => {
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

    const table = page.getByRole('table');
    const tableRows = table.getByRole('row');
    await expect(table).toBeVisible();
    await expect(tableRows).toHaveCount(4); // include header

    await test.step('Enter search query', async () => {
      const searchBox = page.getByRole('searchbox', {
        name: 'Search by keyword',
        exact: true,
      });

      await expect(searchBox).toBeVisible();

      // wait for response so test doesn't fail waiting for debounce
      const searchResp = page.waitForResponse(
        (res) =>
          res.url().includes('/codes') &&
          res.request().url().includes('search=mock+custom') &&
          res.status() === 200
      );
      await searchBox.fill('mock custom');
      await searchResp;
    });

    await test.step('Check search results', async () => {
      await expect(table).toBeVisible();
      await expect(table.getByRole('row')).toHaveCount(2); // custom code and header only
    });
  });

  test('Searching works in tandem with other filters applied', async ({
    page,
    api,
    configurationPage,
  }) => {
    const condition = 'Amebiasis';
    const systems = await api.getSystems();
    const icd10Id = systems.find((s) => s.display_name === 'ICD-10')!.id;
    await test.step('Set up configuration', async () => {
      const config = await api.createConfiguration(condition);

      await api.uploadCustomCodeCsv(config.id, [
        {
          code: 'A06.22',
          display: 'Amebic',
          system_id: icd10Id,
        },
      ]);
    });

    await test.step('Navigate to management page', async () => {
      await page.reload();
      await expect(
        page.getByRole('heading', { name: 'Configurations', level: 1 })
      ).toBeVisible();
      await page.getByRole('link', { name: condition }).click();
      await expect(
        page.getByRole('heading', { name: 'Customize eICR sections' })
      ).toBeVisible();
      await goToManageCodesDevPage(page, configurationPage);
    });

    await test.step('Filter by ICD-10', async () => {
      const codeSystemFilterButton = page.getByTestId('code-system-button');
      const codeSystemOptions = page.getByTestId('code-system-options');

      await expect(codeSystemFilterButton).toBeVisible();
      await codeSystemFilterButton.click();

      const icd10Option = codeSystemOptions.getByRole('option', {
        name: 'ICD-10',
        exact: false,
      });

      const codeSystemResp = page.waitForResponse(
        (res) =>
          res.url().includes('/codes') &&
          res.request().url().includes(`code_systems=${icd10Id}`) &&
          res.status() === 200
      );

      await icd10Option.click();
      await codeSystemResp;

      await page.keyboard.press('Escape');
      await expect(codeSystemFilterButton).toContainText('1 selected');
    });

    const searchText = 'amebi';
    await test.step('Enter search query', async () => {
      const searchBox = page.getByRole('searchbox', {
        name: 'Search by keyword',
        exact: true,
      });

      await expect(searchBox).toBeVisible();

      // wait for response so test doesn't fail waiting for debounce
      const searchResp = page.waitForResponse(
        (res) =>
          res.url().includes('/codes') &&
          res.request().url().includes(`search=${searchText}`) &&
          res.status() === 200
      );
      await searchBox.fill(searchText);
      await searchResp;
    });

    await test.step('Check table results', async () => {
      const table = page.getByRole('table');
      const tableRows = table.getByRole('row');

      await expect(tableRows.nth(1)).toBeVisible(); // make sure table is ready
      const rowCount = await tableRows.count();

      // start at 1 to skip header
      for (let i = 1; i < rowCount; i++) {
        const systemCell = tableRows.nth(i).getByRole('cell').nth(2);
        const descriptionCell = tableRows.nth(i).getByRole('cell').nth(3);
        await expect(systemCell).toHaveText('ICD-10');
        await expect(descriptionCell).toContainText(
          new RegExp(searchText, 'i')
        ); // ignore casing
      }
    });
  });
});

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
    api,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
    await expect(
      page.getByRole('heading', { name: 'Manage codes', level: 2 })
    ).toBeVisible();

    await test.step('Add Alpha-gal Syndrome code set', async () => {
      await page.getByRole('button', { name: '1 Condition code sets' }).click();
      await page
        .getByRole('searchbox', { name: 'Search by condition name' })
        .fill('alph');
      await page
        .getByRole('listitem')
        .filter({ hasText: 'Alpha-gal Syndrome' })
        .hover();
      await page.getByLabel('Add Alpha-gal Syndrome').click();
      await page.getByRole('button', { name: 'Close drawer' }).click();
      await expect(
        page.getByRole('button', { name: '2 Condition code sets' })
      ).toBeVisible();
    });

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

    await test.step('Select code system filter options', async () => {
      const systems = await api.getSystems();
      const cvxId = systems.find((s) => s.display_name === 'CVX')!.id;
      const loincID = systems.find((s) => s.display_name === 'LOINC')!.id;

      const loincFilterResponse = page.waitForResponse(
        (res) =>
          res.url().includes('/codes') &&
          res.request().url().includes(`code_systems=${loincID}`) &&
          res.status() === 200
      );

      await loincOption.click();
      await loincFilterResponse;

      await page.keyboard.press('Escape');
      await expect(codeSystemFilterButton).toContainText('1 selected');

      const cvxFilterResponse = page.waitForResponse(
        (res) =>
          res.url().includes('/codes') &&
          res.request().url().includes(`code_systems=${loincID}`) &&
          res.request().url().includes(`code_systems=${cvxId}`) &&
          res.status() === 200
      );

      await codeSystemFilterButton.click();
      await expect(cvxOption).toBeVisible();

      await cvxOption.click();
      await cvxFilterResponse;

      await page.keyboard.press('Escape');
      await expect(codeSystemFilterButton).toContainText('2 selected');
    });

    await test.step('Check that table results only has LOINC codes', async () => {
      // This condition has no CVX codes which is why only LOINC appear
      const tableRows = page.getByRole('table').getByRole('row');
      await expect(tableRows.nth(1)).toBeVisible(); // make sure table is ready
      const rowCount = await tableRows.count();
      for (let i = 1; i < rowCount; i++) {
        const codeSystemCell = tableRows.nth(i).getByRole('cell').nth(2);
        await expect(codeSystemCell).toHaveText('LOINC');
      }
    });

    await test.step('Ensure "clear selection" button clears filter', async () => {
      await codeSystemFilterButton.click();
      const clearButton = codeSystemOptions.getByRole('option', {
        name: 'Clear selection',
      });
      await expect(clearButton).toBeVisible();
      await clearButton.click();
      await page.keyboard.press('Escape');
      await expect(codeSystemFilterButton).toContainText('Code system');
    });
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
      await expect(
        page.getByRole('button', { name: '2 Condition code sets' })
      ).toBeVisible();
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

    await test.step('Check that table results only has Acanthamoeba codes', async () => {
      const tableRows = page.getByRole('table').getByRole('row');
      await expect(tableRows.nth(1)).toBeVisible(); // make sure table is loaded
      const rowCount = await tableRows.count();
      for (let i = 1; i < rowCount; i++) {
        const sourceCell = tableRows.nth(i).getByRole('cell').nth(4);
        await expect(sourceCell).toHaveText(
          'Acanthamoeba Reporting Specification Grouper'
        );
      }
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
    const table = page.getByRole('table');
    const tableRows = table.getByRole('row');

    await test.step('Check the page on load', async () => {
      await expect(table).toBeVisible();
      await expect(tableRows).toHaveCount(3);
    });

    await test.step('Exclude a code', async () => {
      const checkbox = tableRows.nth(1).getByRole('checkbox');
      await checkbox.click();

      const controlPanel = page.getByTestId('control-panel');
      await expect(controlPanel).toBeVisible();

      await controlPanel.getByRole('button', { name: 'Exclude' }).click();

      const statusCell = tableRows.nth(1).getByRole('cell').last();
      await expect(statusCell).toContainText('Excluded');
    });

    const includedOption = sourceOptions.getByRole('option', {
      name: 'Included',
      exact: false,
    });

    const excludedOption = sourceOptions.getByRole('option', {
      name: 'Excluded',
      exact: false,
    });

    await test.step('Check that both "Include" and "Excluded" options are available', async () => {
      await expect(sourceFilterButton).toBeVisible();
      await sourceFilterButton.click();

      await expect(includedOption).toBeVisible();
      await expect(excludedOption).toBeVisible();
    });

    await test.step('Filter on "Excluded" codes and check result table rows', async () => {
      await excludedOption.click();
      await page.keyboard.press('Escape');
      await expect(sourceFilterButton).toContainText('1 selected');

      await expect(tableRows).toHaveCount(2);
    });
  });

  test('Combination of all filters work together', async ({
    page,
    api,
    configurationPage,
  }) => {
    await test.step('Set up configuration', async () => {
      const condition = 'Anotia';
      const config = await api.createConfiguration(condition);
      const systems = await api.getSystems();
      await api.uploadCustomCodeCsv(config.id, [
        {
          code: '123-4',
          display: 'mock custom code',
          system_id: systems.find((s) => s.display_name === 'Other')!.id,
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

    const associatedCondition = 'Bladder Exstrophy';
    const associatedConditionSearch = 'blad';
    await test.step(`Add ${associatedCondition} code set`, async () => {
      await page.getByRole('button', { name: '1 Condition code sets' }).click();
      await page
        .getByRole('searchbox', { name: 'Search by condition name' })
        .fill(associatedConditionSearch);
      await page
        .getByRole('listitem')
        .filter({ hasText: associatedCondition })
        .hover();
      await page.getByLabel(`Add ${associatedCondition}`).click();
      await page.getByRole('button', { name: 'Close drawer' }).click();
      await expect(
        page.getByRole('button', { name: '2 Condition code sets' })
      ).toBeVisible();
    });

    await test.step('Configure code system filter', async () => {
      const codeSystemFilterButton = page.getByTestId('code-system-button');
      const codeSystemOptions = page.getByTestId('code-system-options');

      const snomedOption = codeSystemOptions.getByRole('option', {
        name: 'SNOMED',
        exact: false,
      });
      const otherOption = codeSystemOptions.getByRole('option', {
        name: 'Other',
        exact: false,
      });

      await expect(codeSystemFilterButton).toBeVisible();
      await codeSystemFilterButton.click();

      await expect(snomedOption).toBeVisible();
      await expect(otherOption).toBeVisible();

      await snomedOption.click();
      await otherOption.click();

      await page.keyboard.press('Escape');
      await expect(codeSystemFilterButton).toHaveText('2 selected');
    });

    await test.step('Configure source filter', async () => {
      const sourceFilterButton = page.getByTestId('source-button');
      const sourceOptions = page.getByTestId('source-options');

      await expect(sourceFilterButton).toBeVisible();
      await sourceFilterButton.click();

      await expect(sourceOptions).toBeVisible();
      await expect(sourceOptions.getByRole('option')).toHaveCount(4); // both RSGs + custom code + clear selection

      // use all 3 options
      const optionCountExcludingClearSelectionButton = 3;
      for (let i = 0; i < optionCountExcludingClearSelectionButton; i++) {
        const option = sourceOptions.getByRole('option').nth(i);
        await expect(option).toBeVisible();
        await option.click();
        await expect(option).toHaveAttribute('aria-selected', 'true');
      }
      await page.keyboard.press('Escape');
      await expect(sourceFilterButton).toHaveText('3 selected');
    });

    await test.step('Configure status filter', async () => {
      const statusFilterButton = page.getByTestId('status-button');
      const statusOptions = page.getByTestId('status-options');
      const includedOption = statusOptions.getByRole('option', {
        name: 'Included',
        exact: false,
      });

      await expect(statusFilterButton).toBeVisible();
      await statusFilterButton.click();
      await expect(statusOptions).toBeVisible();
      await expect(includedOption).toBeVisible();
      await includedOption.click();
      await expect(includedOption).toHaveAttribute('aria-selected', 'true');

      await page.keyboard.press('Escape');
      await expect(statusFilterButton).toHaveText('1 selected');
    });

    await test.step('Check that table has expected results', async () => {
      const table = page.getByRole('table');
      const tableRows = table.getByRole('row');

      // this includes the header row
      await expect(tableRows).toHaveCount(5);

      const sourceCellNumber = 4;
      const sourceCells = tableRows
        .filter({ hasNot: page.getByRole('columnheader') })
        .locator(`td:nth-child(${sourceCellNumber + 1})`);

      const texts = await sourceCells.allTextContents();

      expect(texts.some((t) => t.includes('Custom code'))).toBe(true);
      expect(
        texts.some((t) =>
          t.includes(`${associatedCondition} Reporting Specification Grouper`)
        )
      ).toBe(true);
      expect(
        texts.some((t) => t.includes('Anotia Reporting Specification Grouper'))
      ).toBe(true);
      expect(
        texts.filter((t) =>
          t.includes(`${associatedCondition} Reporting Specification Grouper`)
        )
      ).toHaveLength(2);
    });
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

  test('All filters can be cleared when no results are found', async ({
    page,
    configurationPage,
    configurationsPage,
  }) => {
    const clearButton = page.getByRole('button', {
      name: 'Clear search and filters',
    });
    const codeSystemFilterButton = page.getByTestId('code-system-button');
    const searchBox = page.getByRole('searchbox', {
      name: 'Search by keyword',
      exact: true,
    });
    const table = page.getByRole('table');

    await test.step('Check page on load', async () => {
      const condition = 'Anotia';
      await configurationsPage.createConfiguration(condition);
      await goToManageCodesDevPage(page, configurationPage);
      await expect(
        page.getByRole('heading', { name: 'Manage codes', level: 2 })
      ).toBeVisible();

      await expect(table).toBeVisible();
      await expect(clearButton).not.toBeVisible();
      await expect(page.getByText("You've reached the end.")).toBeVisible();
    });

    await test.step('Configure code system filter', async () => {
      const codeSystemOptions = page.getByTestId('code-system-options');

      const snomedOption = codeSystemOptions.getByRole('option', {
        name: 'SNOMED',
        exact: false,
      });

      await expect(codeSystemFilterButton).toBeVisible();
      await codeSystemFilterButton.click();

      await expect(snomedOption).toBeVisible();

      await snomedOption.click();

      await page.keyboard.press('Escape');
      await expect(codeSystemFilterButton).toHaveText('1 selected');
    });

    await test.step('Enter search query', async () => {
      await expect(searchBox).toBeVisible();

      // wait for response so test doesn't fail waiting for debounce
      const searchResp = page.waitForResponse(
        (res) =>
          res.url().includes('/codes') &&
          res.request().url().includes('search=nothing+to+find') &&
          res.status() === 200
      );
      await searchBox.fill('nothing to find');
      await searchResp;
    });

    await test.step("Use 'clear filters' button", async () => {
      await expect(
        page.getByText('No codes match your search or filters.')
      ).toBeVisible();

      await expect(clearButton).toBeVisible();
      await clearButton.click();

      await expect(searchBox).toHaveValue('');
      await expect(codeSystemFilterButton).toHaveText('Code system');
      await expect(page.getByRole('table')).toBeVisible();
    });
  });
});

test.describe('Codes management - data loading', () => {
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

    const tableRows = page.getByRole('table').getByRole('row');

    await expect(tableRows).toHaveCount(MAX_PAGE_SIZE + 1); // page size + header row

    await tableRows.last().scrollIntoViewIfNeeded();

    // Scrolling down should add `MAX_PAGE_SIZE` to the table
    const expectedRowCountAfterLoad = 2 * MAX_PAGE_SIZE + 1;
    await expect(tableRows).toHaveCount(expectedRowCountAfterLoad);

    // table headers should be sticky
    await expect(tableRows.first()).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });
});
