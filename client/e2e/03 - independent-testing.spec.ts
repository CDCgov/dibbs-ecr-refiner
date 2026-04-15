import { test, expect } from './fixtures/fixtures';
import path from 'path';
import fs from 'fs';
import {
  createAndActivateCovidConfig,
  createAndActivateInfluenzaConfig,
} from './utils';
import { Page } from '@playwright/test';
import { deleteConfigurationArtifacts } from './db';

test.describe('should be able to access independent testing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/configurations');
  });

  test.afterAll(async () => {
    await deleteConfigurationArtifacts('COVID-19');
    await deleteConfigurationArtifacts('Influenza');
  });

  // Resolve the file path relative to the project root
  const filePath = path.resolve(
    process.cwd(),
    'e2e/assets/mon-mothma-two-conditions.zip'
  );

  async function uploadTestFile(page: Page) {
    const independentFlowFileInput = page.locator('input#zip-upload');
    await independentFlowFileInput.setInputFiles(filePath);

    await page.getByText('Refine .zip file').click();
  }

  const ESSENTIAL_HYPERTENSION_SNOMED = '59621000';

  test('should check that the independent test flow handles display of matching configs, missing configs, and a combination of both', async ({
    page,
    makeAxeBuilder,
  }) => {
    // start on home screen
    await expect(
      page.getByRole('heading', { name: 'Configurations' })
    ).toBeVisible();

    // go to independent testing flow
    await page.getByRole('link', { name: 'Testing' }).click();
    await expect(
      page.getByText('Want to refine your own eCR file?')
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await uploadTestFile(page);

    // check for missing configs text
    await expect(
      page.locator('text=have not been configured and will not produce')
    ).toBeVisible();
    await expect(page.getByText('COVID-19')).toBeVisible();
    await expect(page.getByText('Influenza')).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Refine ecr is unavailable
    const startOverButton = page.getByRole('button', { name: 'Start over' });
    await expect(startOverButton).toBeVisible();
    await expect(page.getByRole('button', { name: 'Refine eCR' })).toHaveCount(
      0
    );

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // go home
    await page
      .getByRole('link', { name: 'Link back to the home configurations page' })
      .click();
    await expect(
      page.getByRole('heading', { name: 'Configurations' })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // configure and activate the relevant configs
    await createAndActivateCovidConfig(page);
    await page.getByRole('link', { name: 'Testing' }).click();
    await uploadTestFile(page);

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
    await page
      .getByRole('link', { name: 'Link back to the home configurations page' })
      .click();
    await expect(
      page.getByRole('heading', { name: 'Configurations' })
    ).toBeVisible();

    // configure and activate influenza
    await createAndActivateInfluenzaConfig(page);

    // go to independent testing flow
    await page.getByRole('link', { name: 'Testing' }).click();

    await uploadTestFile(page);

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
    await page.getByRole('link', { name: 'Testing' }).click();

    await uploadTestFile(page);

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
    await page.getByRole('button', { name: 'Refine eCR' }).click();

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
    await page.getByRole('link', { name: 'Testing' }).click();

    // navigate to the place where we're linking to the sample files
    const linkURL = await page
      .getByRole('link', { name: "visit eCR Refiner's repository" })
      .getAttribute('href');
    expect(linkURL).not.toBeNull();
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

    await page
      .getByRole('link', { name: 'Configurations', exact: true })
      .click();
    await page
      .getByRole('link', {
        name: 'COVID-19',
      })
      .click();
    await page.getByText('Test', { exact: true }).click();
    await fileUpload.setInputFiles(filePath);

    await page.getByRole('button', { name: 'Refine .zip file' }).click();
    const inlineFlowCovidResult = await page
      .getByTestId('test-refinement-result')
      .textContent();

    expect(inlineFlowCovidResult).toStrictEqual(independentFlowCovidResult);

    await page
      .getByRole('link', { name: 'Configurations', exact: true })
      .click();

    await page
      .getByRole('link', {
        name: 'Influenza',
      })
      .click();

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

  test('adds a custom code and checks the value gets refined', async ({
    page,
    makeAxeBuilder,
  }) => {
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // use the COVID configuration, or make it if it doesn't exist
    await page.goto('/configurations');

    await expect(
      page.getByRole('heading', { name: 'Configurations' })
    ).toBeVisible();

    await page.goto('/configurations');
    const covidConfig = page.getByText('COVID-19');

    await covidConfig.click();
    await expect(
      page.getByRole('heading', { name: 'COVID-19', exact: true })
    ).toBeVisible();

    const someDraftExists = await createOrNavigateToLatestDraft();

    await expect(
      page.getByRole('heading', { name: 'Build configuration' })
    ).toBeVisible();

    await page.getByRole('button', { name: 'Custom codes' }).click();
    await expect(
      page.getByRole('heading', { name: 'Custom codes' })
    ).toBeVisible();

    const hyperTensionCode = page.locator(
      `text=${ESSENTIAL_HYPERTENSION_SNOMED}`
    );
    const hyperTensionCodeCount = await hyperTensionCode.count();
    if (hyperTensionCodeCount === 0) {
      await createHypertensionCode();
    }

    await page.getByText('Activate').click();

    if (someDraftExists) {
      await page.getByRole('button', { name: 'Switch to version' }).click();
      await page
        .getByRole('button', { name: 'Yes, switch to Version' })
        .click();
    }

    await expect(page.getByText('Configuration activated')).toBeVisible();

    await page.getByRole('link', { name: 'Testing' }).click();
    await expect(page.getByText('Test Refiner')).toBeVisible();

    await uploadTestFile(page);
    await page.getByText('Refine eCR').click();

    await expect(
      page.getByRole('heading', { name: 'eCR refinement results' })
    ).toBeVisible();

    await expect(page.getByText('eICR file size reduced by')).toBeVisible();

    async function createHypertensionCode() {
      await page.getByRole('button', { name: 'Custom codes' }).click();
      await expect(
        page.getByRole('heading', { name: 'Custom codes', level: 3 })
      ).toBeVisible();
      await page.getByRole('button', { name: 'Add new custom code' }).click();
      const submitButton = page.getByRole('button', {
        name: 'Add custom code',
      });
      await page
        .getByRole('textbox', { name: 'Code #' })
        .fill(ESSENTIAL_HYPERTENSION_SNOMED);
      await page.getByLabel('Code system').selectOption('snomed');
      await page
        .getByRole('textbox', { name: 'Code name' })
        .fill('Essential Hypertension');

      await submitButton.click();
      await expect(page.getByText('Custom code added')).toBeVisible();
    }

    async function createOrNavigateToLatestDraft() {
      let someDraftExists = false;
      const goToDraftButton = page.locator('text="Go to draft"');
      const goToDraftButtonCount = await goToDraftButton.count();

      if (goToDraftButtonCount > 0) {
        someDraftExists = true;
        await goToDraftButton.click();
      }

      const createDraftButton = page.locator('text="Draft a new version"');
      const createToDraftButtonCount = await createDraftButton.count();

      if (createToDraftButtonCount > 0) {
        someDraftExists = true;
        await createDraftButton.click();
        await page.getByText('Yes, draft a new version').click();
      }

      return someDraftExists;
    }
  });
});
