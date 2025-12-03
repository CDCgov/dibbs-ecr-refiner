import { test, expect } from './fixtures/fixtures';
import { login, logout } from './utils';

test.describe('Activity log', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('Generate event logs and check activity log page', async ({ page }) => {
    // create a condition
    await page
      .getByRole('button', { name: 'Set up new configuration' })
      .click();
    await page.getByTestId('combo-box-input').click();
    await page.getByTestId('combo-box-input').fill('Zika Virus Disease');
    await page.getByTestId('combo-box-input').press('Tab');
    await page
      .getByRole('option', { name: 'Zika Virus Disease' })
      .press('Enter');
    await page.getByTestId('combo-box-input').press('Tab');
    await page.getByTestId('combo-box-clear-button').press('Tab');
    await page.getByTestId('modalFooter').getByTestId('button').click();
    await expect(
      page.getByRole('heading', { name: 'New configuration created' })
    ).toBeVisible();

    // add / remove some code sets
    await page.getByRole('button', { name: 'Add new code set to' }).click();
    await expect(
      page.getByRole('heading', { name: 'Add condition code sets' })
    ).toBeVisible();

    await page.getByText('Acanthamoeba').click();
    await expect(
      page.getByRole('button', { name: 'Remove Acanthamoeba' })
    ).toBeVisible();

    await page.getByText('Acute Flaccid Myelitis (AFM)').click();
    await expect(
      page.getByRole('button', { name: 'Remove Acute Flaccid Myelitis (AFM)' })
    ).toBeVisible();

    await page
      .getByText('Agricultural Chemicals (Fertilizer) Poisoning')
      .click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Agricultural Chemicals (Fertilizer) Poisoning',
      })
    ).toBeVisible();

    await page.getByText('Alpha-gal Syndrome').click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Alpha-gal Syndrome',
      })
    ).toBeVisible();

    await page.getByText('Amebiasis').click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Amebiasis',
      })
    ).toBeVisible();

    await page.getByText('Anaplasmosis').click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Anaplasmosis',
      })
    ).toBeVisible();

    await page.getByText('Angiostrongyliasis').click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Angiostrongyliasis',
      })
    ).toBeVisible();

    await page.getByText('Animal Bite Injury').click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Animal Bite Injury',
      })
    ).toBeVisible();

    await page.getByText('Anophthalmia').click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Anophthalmia',
      })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Remove Anaplasmosis' })
    ).toBeVisible();
    await page.getByRole('button', { name: 'Remove Anaplasmosis' }).click();

    await page.getByTestId('close-drawer').click();

    // go to activity log page
    await page.getByRole('link', { name: 'Activity Log' }).click();

    // filter by zika
    await page
      .getByLabel('Condition')
      .selectOption(
        'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/2236d7c1-2778-4f1e-bfda-73730632896e'
      );

    // should be 11 items on page 1 (including header)
    await expect(page.getByRole('row')).toHaveCount(11);
    await page.getByRole('button', { name: 'Next' }).click();

    // should be 3 items on page 2 (including header)
    await expect(page.getByRole('row')).toHaveCount(3);
  });
});
