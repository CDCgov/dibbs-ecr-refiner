import { test, expect } from './fixtures/fixtures';
import {
  createAndActivateCovidConfig,
  deleteConfigurationArtifacts,
} from './utils';
import path from 'path';

const ESSENTIAL_HYPERTENSION_SNOMED = '59621000';
const EXPECTED_HYPERTENSION_ELEMENT =
  '<value code="59621000" codeSystem="2.16.840.1.113883.6.96" codeSystemName="SNOMED-CT" displayName="Essential hypertension (disorder)" xsi:type="CD"/>';

const makeCsvContent = (
  rows: { code: string; system: string; name: string }[]
) => {
  const header = 'code_number,code_system,display_name';
  const lines = rows.map((row) => `${row.code},${row.system},${row.name}`);
  return [header, ...lines].join('\n') + '\n';
};

test.describe('Custom code builder flows', () => {
  test('adds, edits, and removes custom codes with validation', async ({
    page,
    makeAxeBuilder,
    configurationPage,
  }) => {
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    const configurationName = configurationPage.getConfigurationName();

    await page.getByRole('link', { name: 'Build' }).click();
    await expect(
      page.getByRole('heading', { name: configurationName, level: 1 })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await page.getByRole('button', { name: 'Custom codes' }).click();
    await expect(
      page.getByRole('heading', { name: 'Custom codes', level: 3 })
    ).toBeVisible();

    await page.getByRole('button', { name: 'Add new custom code' }).click();

    const submitButton = page.getByRole('button', { name: 'Add custom code' });
    await expect(submitButton).toBeDisabled();

    await page.getByRole('textbox', { name: 'Code #' }).fill('CK-10001');
    await page.getByLabel('Code system').selectOption('rxnorm');
    await page
      .getByRole('textbox', { name: 'Code name' })
      .fill('Custom Kitsune');

    await expect(submitButton).toBeEnabled();
    await submitButton.click();
    await expect(page.getByText('Custom code added')).toBeVisible();

    const rowLocator = page
      .locator('table tbody tr')
      .filter({ hasText: 'Custom Kitsune' })
      .first();
    await expect(
      rowLocator.getByRole('cell', { name: 'CK-10001', exact: true })
    ).toBeVisible();

    const editButton = rowLocator.getByRole('button', {
      name: 'Edit custom code Custom Kitsune',
    });
    await editButton.click();

    const modalSaveButton = page.getByRole('button', { name: 'Update' });
    await page
      .getByRole('textbox', { name: 'Code name' })
      .fill('Custom Kitsune Updated');
    await modalSaveButton.click();
    await expect(page.getByText('Custom code updated')).toBeVisible();
    await expect(
      rowLocator.getByRole('cell', {
        name: 'Custom Kitsune Updated',
        exact: true,
      })
    ).toBeVisible();

    const deleteButton = rowLocator.getByRole('button', {
      name: 'Delete custom code Custom Kitsune Updated',
    });
    await deleteButton.click();
    await expect(page.getByText('Deleted code')).toBeVisible();
    await expect(
      page.getByRole('cell', { name: 'Custom Kitsune Updated' })
    ).not.toBeVisible();
  });

  test('uploads CSV, edits preview rows, and undoes the upload', async ({
    page,
    makeAxeBuilder,
    configurationPage,
  }) => {
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    const configurationName = configurationPage.getConfigurationName();

    await expect(
      page.getByRole('heading', { name: configurationName, level: 1 })
    ).toBeVisible();

    await page.getByRole('link', { name: 'Build' }).click();
    await page.getByRole('button', { name: 'Custom codes' }).click();
    await page.getByRole('button', { name: 'Import from CSV' }).click();
    await expect(
      page.getByRole('heading', { name: 'Import from CSV' })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    const suffix = Date.now();
    const csvRows = [
      { code: `csv-${suffix}-1`, system: 'ICD-10', name: 'CSV Row One' },
      { code: `csv-${suffix}-2`, system: 'LOINC', name: 'CSV Row Two' },
    ];
    const csvContent = makeCsvContent(csvRows);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles([
      {
        name: 'custom_codes.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csvContent),
      },
    ]);

    await expect(
      page.getByText('Review the codes below to make sure they are correct')
    ).toBeVisible();

    const previewRowOne = page
      .locator('table tbody tr')
      .filter({ hasText: csvRows[0].name })
      .first();

    await previewRowOne.getByRole('button', { name: 'Edit' }).click();
    const modalCodeInput = page
      .getByRole('textbox', { name: 'Code #' })
      .first();
    await modalCodeInput.fill(`${csvRows[0].code}-updated`);
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(
      page.getByRole('button', { name: 'Undo & delete codes' })
    ).toBeVisible();

    await page.getByRole('searchbox', { name: 'Search codes' }).fill('updated');
    await expect(
      page.getByRole('cell', { name: `${csvRows[0].code}-updated` })
    ).toBeVisible();

    await page.getByRole('searchbox', { name: 'Search codes' }).fill('');
    const refreshedRowTwo = page
      .locator('table tbody tr')
      .filter({ hasText: csvRows[1].name })
      .first();
    await expect(refreshedRowTwo).toBeVisible();

    await refreshedRowTwo.getByRole('button', { name: 'Edit' }).click();
    const previewModalCodeName = page.getByRole('textbox', {
      name: 'Code name',
    });
    await previewModalCodeName.fill('CSV Row Two Edited');
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(page.getByText('Row deleted')).not.toBeVisible();

    await refreshedRowTwo.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByText('Row deleted')).toBeVisible();

    await page.getByRole('button', { name: 'Undo & delete codes' }).click();
    const undoModal = page.getByRole('dialog', {
      name: 'Undo & delete codes',
    });
    const confirmUndo = undoModal.getByRole('button', {
      name: 'Undo & delete codes',
    });
    await expect(confirmUndo).toBeVisible();
    await confirmUndo.click();
    await expect(undoModal).toBeHidden();

    await expect(
      page.getByRole('button', { name: 'Import from CSV' })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
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

    let covidConfig = page.locator('[data-testid="COVID-19-button"]');
    const covidButtonCount = await covidConfig.count();

    let createdNewConfig = false;

    if (covidButtonCount === 0) {
      await createAndActivateCovidConfig(page);
      createdNewConfig = true;
    }

    await page.goto('/configurations');
    covidConfig = page.getByTestId('COVID-19-button');

    await covidConfig.click();
    await expect(
      page.getByRole('heading', { name: 'COVID-19', exact: true })
    ).toBeVisible();

    let someDraftExists = false;
    const goToDraftButton = page.locator('[data-testid="go-to-draft-button"]');
    const goToDraftButtonCount = await goToDraftButton.count();

    if (goToDraftButtonCount > 0) {
      someDraftExists = true;
      await goToDraftButton.click();
    }

    const createDraftButton = page.locator(
      '[data-testid="create-draft-button"]'
    );
    const createToDraftButtonCount = await createDraftButton.count();

    if (createToDraftButtonCount > 0) {
      someDraftExists = true;
      await createDraftButton.click();
      await page.getByText('Yes, draft a new version').click();
    }

    const hyperTensionCode = page.locator(
      `data-testid=${ESSENTIAL_HYPERTENSION_SNOMED}`
    );
    await expect(
      page.getByRole('heading', { name: 'Build configuration' })
    ).toBeVisible();

    await page.getByRole('button', { name: 'Custom codes' }).click();
    await expect(
      page.getByRole('heading', { name: 'Custom codes' })
    ).toBeVisible();

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

    const fileInput = page.locator('input#zip-upload');

    // Resolve the file path relative to the project root
    const filePath = path.resolve(
      process.cwd(),
      'e2e/assets/mon-mothma-two-conditions.zip'
    );

    await fileInput.setInputFiles(filePath);

    await page.getByText('Refine .zip file').click();
    await page.getByText('Refine eCR').click();

    await expect(
      page.getByRole('heading', { name: 'eCR refinement results' })
    ).toBeVisible();

    await page.getByRole('button', { name: 'Show stacked diff' }).click();

    // hypertension element should be retained and show up exactly once
    await expect(page.getByText(EXPECTED_HYPERTENSION_ELEMENT)).toBeVisible();

    // tear down made artifacts if we created it
    if (createdNewConfig) {
      deleteConfigurationArtifacts('COVID-19');
    }

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
  });
});
