import { test, expect } from '@playwright/test';
import { login, logout } from './utils';

test.describe('Adding configurations by initial condition', () => {

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should be able to create a configuration for Acanthamoeba', async ({
    page,
  }) => {
    /// ==========================================================================
    /// Test that a new condition can be added
    /// ==========================================================================
    await page.getByRole('button', { name: 'Set up new condition' }).click();
    await page.getByTestId('combo-box-input').click();
    await page.getByTestId('combo-box-input').fill('Acanthamoeba');
    await page.getByTestId('combo-box-input').press('Tab');
    await page.getByRole('option', { name: 'Acanthamoeba' }).press('Enter');
    await page.getByTestId('combo-box-input').press('Tab');
    await page.getByTestId('combo-box-clear-button').press('Tab');
    await page.getByTestId('modalFooter').getByTestId('button').click();
    await expect(
      page.getByRole('heading', { name: 'New configuration created' })
    ).toBeVisible();

    /// ==========================================================================
    /// Test that the drawer can open and add condition code sets
    /// ==========================================================================
    await page.getByRole('button', { name: 'Add new code set to' }).click();
    await expect(
      page.getByRole('heading', { name: 'Add condition code sets' })
    ).toBeVisible();
    await page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .click();
    await page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .fill('disease');
    await page.getByRole('listitem', { name: 'Balamuthia mandrillaris' }).click();
    await page.getByRole('heading', { name: 'Condition added' }).click();
    await page.getByTestId('close-drawer').click();
    await expect(
      page.getByRole('button', {
        name: 'Balamuthia mandrillaris Disease, 1178 codes in code set',
      })
    ).toBeVisible();

    /// ==========================================================================
    /// Test that custom codes work
    /// ==========================================================================
    await page.getByRole('button', { name: 'Custom codes' }).click();
    await page.getByRole('button', { name: 'Add new custom code' }).click();
    await page.getByRole('textbox', { name: 'Code #' }).click();
    await page.getByRole('textbox', { name: 'Code #' }).fill('1234');
    await page.getByTestId('Select').selectOption('rxnorm');
    await page.getByRole('textbox', { name: 'Code name' }).click();
    await page.getByRole('textbox', { name: 'Code name' }).fill('qwert');
    await page.getByTestId('modalFooter').getByTestId('button').click();
    await expect(
      page
        .locator('div')
        .filter({ hasText: /^Custom code added1234$/ })
        .nth(2)
    ).toBeVisible();
    await expect(
      page.getByRole('cell', { name: 'qwert', exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole('cell', { name: '1234', exact: true })
    ).toBeVisible();
  });

})
