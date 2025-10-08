import { test, expect } from '@playwright/test';
import { login, logout } from './utils';
import { CONFIGURATION_CTA } from '../src/pages/Configurations/utils';
import path from 'path';
import fs from 'fs';

test.describe.serial('should be able to access independent testing', () => {
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
    await expect(
      page.getByText('Want to refine your own eCR file?')
    ).toBeVisible();
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

  test('should be able to refine with the test file', async ({ page }) => {
    /// ==========================================================================
    /// Test independent flow with test file
    /// ==========================================================================

    await page.getByRole('link', { name: /eCR Refiner/i }).click();

    await page.getByRole('link', { name: 'Testing' }).click();

    // Click the "Use test file" button
    const useTestFileButton = page.getByRole('button', {
      name: 'Use test file',
    });
    await expect(useTestFileButton).toBeVisible();
    await useTestFileButton.click();

    // Verify the expected reportable conditions are visible
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:',
        { exact: false }
      )
    ).toBeVisible();

    const covidLi = page.locator('li', { hasText: /^COVID-19$/ });
    await expect(covidLi).toBeVisible();

    const influenzaLi = page.locator('li', { hasText: /^Influenza$/ });
    await expect(influenzaLi).toBeVisible();

    // Click the "Refine eCR" button
    const refineButton = page.getByRole('button', { name: 'Refine eCR' });
    await expect(refineButton).toBeVisible();
    await refineButton.click();

    await expect(page.getByText('eCR refinement results')).toBeVisible();
    await expect(page.getByText('eICR file size reduced by')).toBeVisible();
    await expect(page.getByText('Original eICR')).toBeVisible();
    await expect(page.getByText('Refined eICR')).toBeVisible();
  });

  test('should be able to upload a file, refine, and download results', async ({
    page,
  }) => {
    /// ==========================================================================
    /// Test independent test flow: upload, refine, download
    /// ==========================================================================
    await page.getByRole('link', { name: /eCR Refiner/i }).click();

    await page.getByRole('link', { name: 'Testing' }).click();

    // Locate the file input by its id
    const fileInput = page.locator('input#zip-upload');

    // Resolve the file path relative to the project root
    const filePath = path.resolve(
      process.cwd(),
      'e2e/assets/mon-mothma-two-conditions.zip'
    );

    // Upload the file directly
    await fileInput.setInputFiles(filePath);

    // Optionally, assert the file name shows up in the UI
    await expect(page.getByText('mon-mothma-two-conditions.zip')).toBeVisible();

    // Click the "Upload .zip file" button
    const uploadButton = page.locator('button[data-testid="button"]', {
      hasText: 'Refine .zip file',
    });
    await uploadButton.click();

    // Assert the reportable conditions text is visible
    // Use regex to ignore line breaks and spacing issues
    await expect(
      page.getByText(
        /We found the following reportable condition\(s\) in the RR:/
      )
    ).toBeVisible();

    const covidLi = page.locator('li', { hasText: /^COVID-19$/ });
    await expect(covidLi).toBeVisible();

    const influenzaLi = page.locator('li', { hasText: /^Influenza$/ });
    await expect(influenzaLi).toBeVisible();

    // Locate the button by test id and filter by visible text
    const refineButton = page
      .getByTestId('button')
      .filter({ hasText: 'Refine eCR' });
    await refineButton.click();

    await expect(page.getByText('eCR refinement results')).toBeVisible();
    await expect(page.getByText('eICR file size reduced by')).toBeVisible();
    await expect(page.getByText('Original eICR')).toBeVisible();
    await expect(page.getByText('Refined eICR')).toBeVisible();

    // --- Click "Download results" and verify file download ---
    const [download] = await Promise.all([
      page.waitForEvent('download'), // wait for download to start
      page.locator('button', { hasText: 'Download results' }).click(),
    ]);

    // Save the downloaded file to a temporary path
    const downloadPath = path.resolve(
      process.cwd(),
      'e2e/downloads/results.zip'
    );
    await download.saveAs(downloadPath);

    // Assert that the file exists
    expect(fs.existsSync(downloadPath)).toBeTruthy();
  });
});
