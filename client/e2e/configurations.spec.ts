import path from 'path';
import { test, expect } from './fixtures/fixtures';
import { deleteConfigurationArtifacts } from './db';
import { Page } from '@playwright/test';

async function clearToasts(page: Page) {
  await expect(page.locator('.Toastify__toast')).toHaveCount(0, {
    timeout: 10000,
  });
}

test.describe('Configurations', () => {
  test.beforeEach(async () => await deleteConfigurationArtifacts('COVID-19'));
  test.afterEach(async () => await deleteConfigurationArtifacts('COVID-19'));
  test('Successful building and activation', async ({
    page,
    makeAxeBuilder,
  }) => {
    const condition = 'COVID-19';

    await expect(
      page.getByRole('heading', {
        name: 'Configurations',
        exact: true,
        level: 1,
      })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // create config
    await page
      .getByRole('button', { name: 'Set up new configuration' })
      .click();
    await page.getByRole('combobox', { name: 'Select condition' }).click();
    await page
      .getByRole('combobox', { name: 'Select condition' })
      .fill('covid');
    await page.getByRole('option', { name: condition }).click();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await page.getByRole('button', { name: 'Set up configuration' }).click();

    // Add a condition code set
    await expect(
      page.getByRole('heading', { name: condition, level: 1 })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await page.getByLabel('Code system').selectOption('SNOMED');
    await page
      .getByRole('button', { name: 'Add new code set to configuration' })
      .click();
    await page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .fill('agri');
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await page
      .getByRole('listitem')
      .filter({ hasText: 'Agricultural Chemicals (Fertilizer) Poisoning' })
      .click();
    await page.getByRole('button', { name: 'Close drawer' }).click();

    // Configure a custom code
    await page.getByRole('button', { name: 'Custom codes' }).click();
    await page.getByRole('button', { name: 'Add new custom code' }).click();
    await page.getByLabel('Code #').fill('my-custom code!');
    await page.getByLabel('Code system').selectOption('snomed');
    await page.getByLabel('Code name').fill('123-! #-$$$');
    await expect(
      page.getByRole('button', { name: 'Add custom code' })
    ).toBeEnabled();
    await page.getByRole('button', { name: 'Add custom code' }).click();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Configure sections
    await page.getByRole('button', { name: 'Sections' }).click();
    await page
      .getByRole('checkbox', { name: 'Include Admission Diagnosis' })
      .click();
    await expect(
      page.getByRole('checkbox', { name: 'Include Admission Diagnosis' })
    ).not.toBeChecked();
    await page
      .getByRole('switch', { name: 'Refine & optimize Admission Medications' })
      .click();
    await expect(
      page.getByRole('switch', {
        name: 'Preserve & retain all data for Admission Medications',
      })
    ).not.toBeChecked();
    await page
      .getByRole('switch', {
        name: 'Toggle to refine or retain the narrative block in the Chief Complaint section',
      })
      .click();
    await expect(
      page.getByRole('switch', {
        name: 'Toggle to refine or retain the narrative block in the Chief Complaint section',
      })
    ).not.toBeChecked();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // check the two that should not be toggleable
    await expect(
      page.getByRole('checkbox', {
        name: 'Include Emergency Outbreak Information section rules in refined document.',
      })
    ).toBeDisabled();
    await expect(
      page.getByRole('checkbox', {
        name: 'Include Reportability Response Information section rules in refined document.',
      })
    ).toBeDisabled();

    // Custom section
    await page.getByRole('button', { name: 'Add custom section' }).click();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await page
      .getByLabel('Display name (for this section)')
      .fill('my custom section');
    await page.getByLabel('LOINC code').fill('custom section code');
    await page.getByRole('button', { name: 'Add section' }).click();
    await expect(
      page.getByRole('switch', {
        name: 'Toggle to refine or retain the narrative block in the my custom section section',
      })
    ).not.toBeChecked();

    // TODO: Fix this
    // const downloadPromise = page.waitForEvent('download');
    // await page.getByRole('link', { name: 'Export configuration' }).click();
    // const download = await downloadPromise;
    await page.getByRole('link', { name: 'Test', exact: true }).click();
    await expect(
      page.getByRole('heading', { name: 'Test configuration' })
    ).toBeVisible();

    // upload file and run test
    const filePath = path.resolve(
      process.cwd(),
      'e2e/assets/mon-mothma-two-conditions.zip'
    );
    await page.locator('input#zip-upload').setInputFiles(filePath);
    await page.getByText('Refine .zip file').click();
    await expect(page.getByText('eICR file size reduced by')).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Download results' })
    ).toBeVisible();

    // Back to build and try deleting things
    await page.getByRole('link', { name: 'Build' }).click();
    await clearToasts(page);
    await page
      .getByRole('button', {
        name: 'View TES code set information for Agricultural Chemicals (Fertilizer) Poisoning',
      })
      .hover();
    await expect(
      page.getByRole('button', {
        name: 'Delete code set Agricultural Chemicals (Fertilizer) Poisoning',
      })
    ).toBeVisible();
    await page
      .getByRole('button', {
        name: 'Delete code set Agricultural Chemicals (Fertilizer) Poisoning',
      })
      .click();

    // custom codes
    await page.getByRole('button', { name: 'Custom codes' }).click();
    await page
      .getByRole('button', { name: 'Delete custom code 123-! #-$$$' })
      .click();
    await expect(page.getByText('123-! #-$$$')).not.toBeVisible();

    // sections
    await page.getByRole('button', { name: 'Sections' }).click();
    await page
      .getByRole('button', { name: 'Delete custom section my custom section' })
      .click();
    await expect(page.getByText('my custom section')).not.toBeVisible();

    // activate
    await page.getByRole('link', { name: 'Activate' }).click();
    await page.getByRole('button', { name: 'Turn on configuration' }).click();
    await page
      .getByRole('button', { name: 'Yes, turn on configuration' })
      .click();
    await expect(
      page.getByRole('button', { name: 'Turn off current version' })
    ).toBeVisible();

    // new draft
    await page.getByRole('link', { name: 'Build' }).click();
    await expect(
      page.getByRole('heading', { name: 'Build configuration', level: 2 })
    ).toBeVisible();

    // TODO: check that nothing is editable

    await page.getByRole('button', { name: 'Draft a new version' }).click();
    await expect(page.getByRole('paragraph')).toContainText('Version 1');
    await expect(page.getByRole('paragraph')).toContainText('Version 2');
    await page
      .getByRole('button', { name: 'Yes, draft a new version' })
      .click();

    await expect(page.getByText('Status: Version 1 active')).toBeVisible();
    await expect(page.getByText('Editing: Version 2')).toBeVisible();

    await page.getByRole('link', { name: 'Activate' }).click();
    await expect(page.getByText('Switch to version 2')).toBeVisible();
    await expect(page.getByText('Turn off configuration')).toBeVisible();

    await page.getByRole('button', { name: 'Switch to version 2' }).click();
    await expect(
      page.getByText("You're about to stop Version 1 and start Version 2")
    ).toBeVisible();
    await page
      .getByRole('button', { name: 'Yes, switch to Version 2' })
      .click();
    await expect(page.getByText('Status: Version 2 active')).toBeVisible();
    await expect(page.getByText('Turn off current version')).toBeVisible();
  });
});
