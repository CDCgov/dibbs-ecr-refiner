import path from 'path';
import { test, expect } from './fixtures/fixtures';
import { deleteConfigurationArtifacts } from './db';

test.describe('Configuration detail flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await deleteConfigurationArtifacts('COVID-19');
  });
  test.afterEach(async () => {
    await deleteConfigurationArtifacts('COVID-19');
  });

  test('User successfully builds and activates a configuration', async ({
    page,
    makeAxeBuilder,
    configurationsPage,
    configurationPage,
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

    // Create config
    await configurationsPage.createConfiguration(condition);

    // Add a condition code set
    await expect(
      page.getByRole('heading', { name: condition, level: 1 })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await page.getByLabel('Code system').selectOption('SNOMED');
    await configurationPage.addCodeSet(
      'agri',
      'Agricultural Chemicals (Fertilizer) Poisoning'
    );

    // Configure a custom code
    await page.getByRole('button', { name: 'Custom codes' }).click();
    await configurationPage.addCustomCode(
      'my-custom code!',
      'snomed',
      '123-! #-$$$'
    );
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

    // Check the two that should not be toggleable
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

    // Navigate to Test page and run test
    await page.getByRole('link', { name: 'Test', exact: true }).click();
    await expect(
      page.getByRole('heading', { name: 'Test configuration' })
    ).toBeVisible();

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

    // Back to build and delete things
    await page.getByRole('link', { name: 'Build' }).click();
    await configurationPage.deleteCodeSet(
      'Agricultural Chemicals (Fertilizer) Poisoning'
    );

    await page.getByRole('button', { name: 'Custom codes' }).click();
    await configurationPage.deleteCustomCode('123-! #-$$$');
    await expect(page.getByText('123-! #-$$$')).not.toBeVisible();

    await page.getByRole('button', { name: 'Sections' }).click();
    await page
      .getByRole('button', { name: 'Delete custom section my custom section' })
      .click();
    await expect(page.getByText('my custom section')).not.toBeVisible();

    // Activate
    await page.getByRole('link', { name: 'Activate' }).click();
    await configurationPage.activateConfiguration();
    await expect(
      page.getByRole('button', { name: 'Turn off current version' })
    ).toBeVisible();

    // Draft a new version
    await page.getByRole('link', { name: 'Build' }).click();
    await expect(
      page.getByRole('heading', { name: 'Build configuration', level: 2 })
    ).toBeVisible();

    await page.getByRole('button', { name: 'Draft a new version' }).click();
    await expect(page.getByRole('paragraph')).toContainText('Version 1');
    await expect(page.getByRole('paragraph')).toContainText('Version 2');
    await page
      .getByRole('button', { name: 'Yes, draft a new version' })
      .click();

    await expect(page.getByText('Status: Version 1 active')).toBeVisible();
    await expect(page.getByText('Editing: Version 2')).toBeVisible();

    // Switch to version 2
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
