import { test, expect } from '@playwright/test';
import { login, logout } from './utils';
import { CONFIGURATION_CTA } from '../src/pages/Configurations/utils';

test.describe('Independent testing flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('should check that the independent test flow handles display of matching configs, missing configs, and a combination of both', async ({
    page,
  }) => {
    // start on home screen
    await expect(
      page.getByText('Your reportable condition configurations')
    ).toBeVisible();

    // go to independent testing flow
    await page.getByRole('link', { name: 'Testing' }).click();
    await page.getByRole('button', { name: 'Use test file' }).click();

    // check for missing configs text
    await expect(
      page.locator('text=have not been configured and will not produce')
    ).toBeVisible();
    await expect(page.getByText('COVID-19')).toBeVisible();
    await expect(page.getByText('Influenza')).toBeVisible();

    // Refine ecr is unavailable
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeVisible();
    await expect(page.getByRole('button', { name: 'Refine eCR' })).toHaveCount(
      0
    );

    // go home
    await page.getByRole('link', { name: 'eCR Refiner' }).click();
    await expect(
      page.getByText('Your reportable condition configurations')
    ).toBeVisible();

    // configure covid-19
    await page.getByRole('button', { name: CONFIGURATION_CTA }).click();
    await page.getByTestId('combo-box-input').click();
    await page.getByTestId('combo-box-input').fill('COVID-19');
    await page.getByTestId('combo-box-input').press('Tab');
    await page.getByRole('option', { name: 'COVID-19' }).press('Enter');
    await page.getByRole('button', { name: 'Set up configuration' }).click();
    await expect(page.getByText('Build configuration')).toBeVisible();

    // go to independent testing flow
    await page.getByRole('link', { name: 'Testing' }).click();
    await page.getByRole('button', { name: 'Use test file' }).click();

    // check for matching config text
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();
    await expect(
      page.getByRole('listitem').filter({ hasText: 'COVID-' })
    ).toBeVisible();

    // check for missing configs text
    await expect(
      page.locator('text=have not been configured and will not produce')
    ).toBeVisible();
    await expect(
      page.getByRole('listitem').filter({ hasText: 'Influenza' })
    ).toBeVisible();

    // both buttons should be available
    await expect(
      page.getByRole('button', { name: 'Refine eCR' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeVisible();

    // click start over
    await page.getByRole('button', { name: 'Start over' }).click();
    await expect(page.getByText("Don't have a file ready?")).toBeVisible();

    // go home
    await page.getByRole('link', { name: 'eCR Refiner' }).click();
    await expect(
      page.getByText('Your reportable condition configurations')
    ).toBeVisible();

    // configure influenza
    await page.getByRole('button', { name: CONFIGURATION_CTA }).click();
    await page.getByTestId('combo-box-input').click();
    await page.getByTestId('combo-box-input').fill('Influenza');
    await page.getByTestId('combo-box-input').press('Tab');
    await page
      .getByRole('option', { name: 'Influenza', exact: true })
      .press('Enter');
    await page.getByRole('button', { name: 'Set up configuration' }).click();
    await expect(page.getByText('Build configuration')).toBeVisible();

    // go to independent testing flow
    await page.getByRole('link', { name: 'Testing' }).click();
    await page.getByRole('button', { name: 'Use test file' }).click();

    // check that only matching configs were found
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeVisible();
    await expect(
      page.getByRole('listitem').filter({ hasText: 'COVID-' })
    ).toBeVisible();
    await expect(
      page.getByRole('listitem').filter({ hasText: 'Influenza' })
    ).toBeVisible();

    await expect(
      page.locator('text=have not been configured and will not produce')
    ).toHaveCount(0);

    // both buttons should be available
    await expect(
      page.getByRole('button', { name: 'Refine eCR' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeVisible();
  });
});
