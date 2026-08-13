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

test.describe('Codes management (WIP)', () => {
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

      await page.getByLabel('Code', { exact: true }).fill(code);
      await page.getByLabel('Code system').selectOption({ label: system });
      await page.getByLabel('Display name').fill(name);
      await page.getByRole('button', { name: 'Add custom code' }).click();
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
