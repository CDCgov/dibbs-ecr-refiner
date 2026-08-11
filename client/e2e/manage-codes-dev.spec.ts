/**
 * 👉 NOTE: This file is temporary. Once the `/manage-codes/view` route makes it into the
 * configuration flow this file's name will be changed or the code in the file
 * will be moved into the `configuration.spec.ts` file
 */

import { test, expect } from './fixtures';
import { clearDb } from './db';
import { Page } from '@playwright/test';
import { ConfigurationPage } from './pages/ConfigurationPage';

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

  test('Unaltered page layout check', async ({
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

    await expect(page.getByTestId('codes-included-display')).toHaveText(
      '2 of 2 codes included'
    );
    await expect(page.getByText('0 excluded')).toBeVisible();
    await expect(page.getByText('0 custom')).toBeVisible();
    await expect(page.getByText('1 condition code sets')).toBeVisible();
    await expect(page.getByText("You've reached the end")).toBeVisible();
  });

  test('Individual codes can be toggled to be included/excluded', async ({
    page,
    configurationsPage,
    configurationPage,
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
  });

  test('Individual custom codes can be added, edited, and deleted', async ({
    page,
    configurationsPage,
    configurationPage,
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
  });

  test.skip('Condition code sets can be added and deleted', async ({
    page,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
  });

  test.skip('More codes load into view as user scrolls down', async ({
    page,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'Anotia';
    await configurationsPage.createConfiguration(condition);
    await goToManageCodesDevPage(page, configurationPage);
  });
});
