import { test, expect } from './fixtures/fixtures';
import { login, logout } from './utils';
import { CONFIGURATION_CTA } from '../src/pages/Configurations/utils';
import path from 'path';
import fs from 'fs';
import { Page } from '@playwright/test';

test.describe.serial('should be able to access independent testing', () => {
  // Resolve the file path relative to the project root
  const filePath = path.resolve(
    process.cwd(),
    'e2e/assets/mon-mothma-two-conditions.zip'
  );
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await login(page);
  });

  test.afterAll(async () => {
    await logout(page);
  });

  test('should check that the independent test flow handles display of matching configs, missing configs, and a combination of both', async ({
    page,
    makeAxeBuilder,
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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    const fileInput = page.locator('input#zip-upload');

    // Upload the file directly
    await fileInput.setInputFiles(filePath);

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Optionally, assert the file name shows up in the UI
    await expect(page.getByText('mon-mothma-two-conditions.zip')).toBeVisible();
    await page.getByText('Refine .zip file').click();

    // check for missing configs text
    await expect(
      page.locator('text=have not been configured and will not produce')
    ).toBeVisible();
    await expect(page.getByText('COVID-19')).toBeVisible();
    await expect(page.getByText('Influenza')).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Refine ecr is unavailable
    await expect(
      page.getByRole('button', { name: 'Start over' })
    ).toBeVisible();
    await expect(page.getByRole('button', { name: 'Refine eCR' })).toHaveCount(
      0
    );

    // go home
    await page.getByRole('link', { name: 'DIBBs eCR Refiner' }).click();
    await expect(
      page.getByText('Your reportable condition configurations')
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

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

    const independentFlowFileInput = page.locator('input#zip-upload');
    await independentFlowFileInput.setInputFiles(filePath);

    await page.getByRole('button', { name: 'Refine .zip file' }).click();

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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // click start over
    await page.getByRole('button', { name: 'Start over' }).click();

    // go home
    await page.getByRole('link', { name: 'DIBBs eCR Refiner' }).click();
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

    await independentFlowFileInput.setInputFiles(filePath);
    await page.getByRole('button', { name: 'Refine .zip file' }).click();

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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('should be able to upload a file, refine, and download results', async ({
    page,
    makeAxeBuilder,
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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

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

  test('should be able to see the generated files for jurisdictions to test', async ({
    page,
  }) => {
    await page.getByRole('link', { name: /eCR Refiner/i }).click();
    await page.getByRole('link', { name: 'Testing' }).click();

    // navigate to the place where we're linking to the sample files
    const linkURL = await page
      .getByRole('link', { name: "visit eCR Refiner's repository" })
      .getAttribute('href');
    expect(linkURL).not.toBeNull();
    await page.goto(linkURL as string);

    // Check that the default file is there
    await expect(
      page.getByRole('link', {
        name: 'APHL_eCR_Refiner_COVID_Influenza_Sample_Files.zip',
      })
    ).toBeVisible();
  });

  test('refinement percentages between the two flows should match', async ({
    page,
  }) => {
    await page.getByRole('link', { name: 'Testing' }).click();

    const fileUpload = page.locator('input#zip-upload');
    await fileUpload.setInputFiles(filePath);

    await page.getByRole('button', { name: 'Refine .zip file' }).click();
    await page.getByRole('button', { name: 'Refine eCR' }).click();

    await page.selectOption('select#condition-select', { label: 'COVID-19' });
    const independentFlowCovidResult = await page
      .getByTestId('test-refinement-result')
      .textContent();

    await page.selectOption('select#condition-select', { label: 'Influenza' });
    const independentFlowInfluenzaResult = await page
      .getByTestId('test-refinement-result')
      .textContent();

    await page.getByRole('link', { name: 'Configurations' }).click();
    await page.getByRole('cell', { name: 'COVID-19', exact: true }).click();
    await page.getByText('Test', { exact: true }).click();
    await fileUpload.setInputFiles(filePath);

    await page.getByRole('button', { name: 'Refine .zip file' }).click();
    const inlineFlowCovidResult = await page
      .getByTestId('test-refinement-result')
      .textContent();

    expect(inlineFlowCovidResult).toStrictEqual(independentFlowCovidResult);

    await page.getByRole('link', { name: 'Configurations' }).click();
    await page.getByRole('cell', { name: 'Influenza', exact: true }).click();

    await page.getByText('Test', { exact: true }).click();
    await fileUpload.setInputFiles(filePath);

    await page.getByRole('button', { name: 'Refine .zip file' }).click();
    const inlineFlowInfluenzaResult = await page
      .getByTestId('test-refinement-result')
      .textContent();

    expect(independentFlowInfluenzaResult).toStrictEqual(
      inlineFlowInfluenzaResult
    );
  });
});
