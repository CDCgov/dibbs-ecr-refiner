import { test, expect } from './fixtures/fixtures';
import { deleteConfigurationArtifacts } from './db';
import { uploadMonmothmaTestFile } from './utils';

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

    const additionalCodeSetName =
      'Agricultural Chemicals (Fertilizer) Poisoning';

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
    await configurationPage.addCodeSet('agri', additionalCodeSetName);

    // Configure a custom code
    await page.getByRole('button', { name: 'Custom codes' }).click();
    const customCodeName = 'my-custom code!';
    const customCodeSystem = 'snomed';
    const customCode = '123-! #-$$$';

    await configurationPage.addCustomCode(
      customCodeName,
      customCodeSystem,
      customCode
    );
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Configure sections
    await page.getByRole('button', { name: 'Sections' }).click();
    const admissionDiagnosisCheckboxText = 'Include Admission Diagnosis';
    await page
      .getByRole('checkbox', { name: admissionDiagnosisCheckboxText })
      .click();
    await expect(
      page.getByRole('checkbox', { name: admissionDiagnosisCheckboxText })
    ).not.toBeChecked();

    const admissionMedicationsText = 'Admission Medications';
    await page
      .getByRole('switch', {
        name: `Refine & optimize ${admissionMedicationsText}`,
      })
      .click();
    await expect(
      page.getByRole('switch', {
        name: `Preserve & retain all data for ${admissionMedicationsText}`,
      })
    ).not.toBeChecked();

    const chiefComplaintSwitchText =
      'Toggle to refine or retain the narrative block in the Chief Complaint section';
    const chiefComplaintSwitch = page.getByRole('switch', {
      name: chiefComplaintSwitchText,
    });
    await chiefComplaintSwitch.click();
    await expect(chiefComplaintSwitch).not.toBeChecked();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Check the two that should not be toggleable
    const emergencyOutbreakIncludeCheckboxText =
      'Include Emergency Outbreak Information section rules in refined document.';
    await expect(
      page.getByRole('checkbox', {
        name: emergencyOutbreakIncludeCheckboxText,
      })
    ).toBeDisabled();

    const reportabilityResponseIncludeCheckboxText =
      'Include Reportability Response Information section rules in refined document.';
    await expect(
      page.getByRole('checkbox', {
        name: reportabilityResponseIncludeCheckboxText,
      })
    ).toBeDisabled();

    // Custom section
    const customSectionName = 'My custom section!';
    const customSectionCode = 'custom section code';

    await page.getByRole('button', { name: 'Add custom section' }).click();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await page
      .getByLabel('Display name (for this section)')
      .fill(customSectionName);
    await page.getByLabel('LOINC code').fill(customSectionCode);
    await page.getByRole('button', { name: 'Add section' }).click();
    await expect(
      page.getByRole('switch', {
        name: `Toggle to refine or retain the narrative block in the ${customSectionName} section`,
      })
    ).not.toBeChecked();

    // Navigate to Test page and run test
    await page.getByRole('link', { name: 'Test', exact: true }).click();
    await expect(
      page.getByRole('heading', { name: 'Test configuration' })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await uploadMonmothmaTestFile(page);
    await expect(page.getByText('eICR file size reduced by')).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Download results' })
    ).toBeVisible();

    // Back to build and delete things
    await page.getByRole('link', { name: 'Build' }).click();
    await configurationPage.deleteCodeSet(additionalCodeSetName);

    await page.getByRole('button', { name: 'Custom codes' }).click();
    await configurationPage.deleteCustomCode(customCode);
    await expect(page.getByText(customCode)).not.toBeVisible();

    await page.getByRole('button', { name: 'Sections' }).click();
    await page
      .getByRole('button', {
        name: `Delete custom section ${customSectionName}`,
      })
      .click();
    await expect(
      page.getByRole('table').getByText(customSectionName)
    ).not.toBeVisible();

    // Activate
    await page.getByRole('link', { name: 'Activate' }).click();
    await configurationPage.activateConfiguration();
    await expect(
      page.getByRole('button', { name: 'Turn off current version' })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Draft a new version
    await page.getByRole('link', { name: 'Build' }).click();
    await expect(
      page.getByRole('heading', { name: 'Build configuration', level: 2 })
    ).toBeVisible();

    await page.getByRole('button', { name: 'Draft a new version' }).click();
    await expect(page.getByRole('paragraph')).toContainText('Version 1');
    await expect(page.getByRole('paragraph')).toContainText('Version 2');
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
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

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await page
      .getByRole('button', { name: 'Yes, switch to Version 2' })
      .click();
    await expect(page.getByText('Status: Version 2 active')).toBeVisible();
    await expect(page.getByText('Turn off current version')).toBeVisible();
  });
});
