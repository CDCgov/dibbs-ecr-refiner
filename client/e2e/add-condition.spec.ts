import { test, expect } from '@playwright/test';
import { login, logout, refreshDatabase } from './utils';

// Force all tests in this file to run sequentially
test.describe.configure({ mode: 'serial' });

test.beforeEach(async ({ page }) => {
  refreshDatabase();
  await login(page);
});

test.afterEach(async ({ page }) => {
  await logout(page);
});

test('should be able to create a configuration for Acanthamoeba', async ({
  page,
}) => {
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
});
