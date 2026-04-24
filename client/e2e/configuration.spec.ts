import { test, expect } from './fixtures';
import { deleteAllConfigurations } from './db';

test.describe('Configuration detail flow', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await deleteAllConfigurations();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await deleteAllConfigurations();
  });

  test('Individual custom code workflow', async ({
    page,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'Amebiasis';
    await configurationsPage.createConfiguration(condition);
    await configurationPage.goToBuildTab();
    await page.getByRole('button', { name: 'Custom codes' }).click();

    const customCode1 = {
      code: '12-! 345#',
      system: 'other',
      name: 'original code 1~',
    };

    const customCode2 = {
      code: '123-456',
      system: 'loinc',
      name: 'original code 2+ =',
    };

    await test.step('Adding a unique code', async () => {
      await configurationPage.addCustomCode(
        customCode1.code,
        customCode1.system,
        customCode1.name
      );
      await expect(
        page.getByRole('table').getByText(customCode1.code)
      ).toBeVisible();

      await configurationPage.addCustomCode(
        customCode2.code,
        customCode2.system,
        customCode2.name
      );
      await expect(
        page.getByRole('table').getByText(customCode2.code)
      ).toBeVisible();
    });

    const newCode = 'test';

    await test.step('Editing a custom code shows an error when an already used code is entered', async () => {
      // try using an already taken code
      await configurationPage.editCustomCode(customCode1.name, {
        newCode: customCode2.code,
      });

      // try navigating away from the input and we'll see the error
      await page.getByLabel('Code name').click();

      const expectedError = page.getByText(
        `The code "${customCode2.code}" already exists.`
      );
      const updateButton = page.getByRole('button', { name: 'Update' });

      await expect(expectedError).toBeVisible();
      await expect(updateButton).toBeDisabled();

      // change the text and the error should go away
      await page.getByLabel('Code #').fill(newCode);
      await page.getByLabel('Code name').click();
      await expect(expectedError).not.toBeVisible();
      await expect(updateButton).toBeEnabled();

      // reassign the code data
      customCode1.code = newCode;

      await updateButton.click();
    });

    await test.step('Deleting a custom code removes it from the table', async () => {
      const deleteButton = page.getByRole('button', {
        name: `Delete custom code ${customCode1.name}`,
      });
      await expect(deleteButton).toBeVisible();
      await configurationPage.deleteCustomCode(customCode1.name);
      await expect(deleteButton).not.toBeVisible();
      await expect(
        page.getByRole('table').getByText(customCode1.name)
      ).not.toBeVisible();
    });

    await test.step('Attempting to add an existing code will display an error', async () => {
      const addNewCustomCodeButton = page.getByRole('button', {
        name: 'Add new custom code',
      });
      await expect(addNewCustomCodeButton).toBeEnabled();
      await addNewCustomCodeButton.click();

      const newSystem = 'cvx';
      const newCode = 'random-code12';

      const expectedError = page.getByText(
        `The code "${customCode2.code}" already exists.`
      );
      const addButton = page.getByRole('button', { name: 'Add custom code' });

      // fill in form
      await page.getByLabel('Code #').fill(customCode2.code);
      await page.getByLabel('Code system').selectOption(customCode2.system);
      await page.getByLabel('Code name').fill(customCode2.name);

      await expect(expectedError).toBeVisible();
      await expect(addButton).not.toBeEnabled();

      await page.getByLabel('Code #').fill(newCode);
      await page.getByLabel('Code system').selectOption(newSystem);
      await page.getByLabel('Code name').click();
      await expect(expectedError).not.toBeVisible();
      await expect(addButton).toBeEnabled();
      await addButton.click();

      const table = page.getByRole('table');
      await expect(table).toBeVisible();
      await expect(table.getByText(newCode)).toBeVisible();
      await expect(table.getByText(newSystem)).toBeVisible();
    });
  });

  test('Uploaded file for inline testing has no conditions matching selected configuration', async ({
    page,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'Cancer';
    await configurationsPage.createConfiguration(condition);
    await expect(
      page.getByRole('heading', { name: condition, level: 1 })
    ).toBeVisible();

    await configurationPage.goToTestTab();
    await configurationPage.uploadInlineTestEcrFile();
    await expect(
      page.getByRole('heading', { name: 'Error', level: 2 })
    ).toBeVisible();
    await expect(
      page.getByText(`The condition '${condition}' was not found`)
    ).toBeVisible();
    await page.getByRole('button', { name: 'Try again' }).click();
    await expect(
      page.getByText('Want to refine your own eCR file?')
    ).toBeVisible();
  });

  test('User successfully builds and activates a configuration', async ({
    page,
    makeAxeBuilder,
    configurationsPage,
    configurationPage,
  }) => {
    const condition = 'COVID-19';

    const customCodeName = 'my-custom code!';
    const customCodeSystem = 'snomed';
    const customCode = '123-! #-$$$';

    const customSectionName = 'My custom section!';
    const customSectionCode = 'custom section code';

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

    await test.step('Create configuration', async () => {
      await configurationsPage.createConfiguration(condition);
      await expect(
        page.getByRole('heading', { name: condition, level: 1 })
      ).toBeVisible();
    });

    await test.step('Add a code set', async () => {
      await expect(
        page.getByRole('heading', { name: condition, level: 1 })
      ).toBeVisible();
      await expect(makeAxeBuilder).toHaveNoAxeViolations();
      await page.getByLabel('Code system').selectOption('SNOMED');
      await configurationPage.addCodeSet('agri', additionalCodeSetName);
    });

    await test.step('Configure a custom code', async () => {
      await page.getByRole('button', { name: 'Custom codes' }).click();
      await configurationPage.addCustomCode(
        customCode,
        customCodeSystem,
        customCodeName
      );
      await expect(makeAxeBuilder).toHaveNoAxeViolations();
    });

    await test.step('Configure standard sections', async () => {
      await test.step('Select and check options', async () => {
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
      });

      await test.step('Check unavailable options are disabled', async () => {
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
      });
    });

    await test.step('Configure custom sections', async () => {
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
    });

    await test.step('Run inline test', async () => {
      await configurationPage.goToTestTab();

      await expect(makeAxeBuilder).toHaveNoAxeViolations();

      await configurationPage.uploadInlineTestEcrFile();
      await expect(page.getByText('eICR file size reduced by')).toBeVisible();
      await expect(
        page.getByRole('button', { name: 'Download results' })
      ).toBeVisible();
    });

    await test.step('Delete custom codes', async () => {
      await configurationPage.goToBuildTab();
      await configurationPage.deleteCodeSet(additionalCodeSetName);

      await page.getByRole('button', { name: 'Custom codes' }).click();
      await configurationPage.deleteCustomCode(customCodeName);
      await expect(page.getByText('Deleted code')).toBeVisible();
      await expect(
        page.getByRole('table').getByText(customCodeName)
      ).not.toBeVisible();
    });

    await test.step('Delete custom section', async () => {
      await page.getByRole('button', { name: 'Sections' }).click();
      await page
        .getByRole('button', {
          name: `Delete custom section ${customSectionName}`,
        })
        .click();
      await expect(
        page.getByRole('table').getByText(customSectionName)
      ).not.toBeVisible();
    });

    await test.step('Activate configuration', async () => {
      await configurationPage.goToActivateTab();
      await configurationPage.activateConfiguration();
      await expect(
        page.getByRole('button', { name: 'Turn off current version' })
      ).toBeVisible();

      await expect(makeAxeBuilder).toHaveNoAxeViolations();
    });

    await test.step('Draft new configuration version', async () => {
      await configurationPage.goToBuildTab();
      await page.getByRole('button', { name: 'Draft a new version' }).click();
      await expect(page.getByRole('paragraph')).toContainText('Version 1');
      await expect(page.getByRole('paragraph')).toContainText('Version 2');
      await expect(makeAxeBuilder).toHaveNoAxeViolations();
      await page
        .getByRole('button', { name: 'Yes, draft a new version' })
        .click();

      await expect(
        page.getByRole('heading', { name: 'Build configuration', level: 2 })
      ).toBeVisible();
      await expect(page.getByText('Status: Version 1 active')).toBeVisible();
      await expect(page.getByText('Editing: Version 2')).toBeVisible();
    });

    await test.step('Upload custom code CSV', async () => {
      await page.getByRole('button', { name: 'Custom codes' }).click();
      await page.getByRole('button', { name: 'Import from CSV' }).click();
      await expect(
        page.getByRole('heading', {
          name: 'Import from CSV',
          exact: true,
          level: 2,
        })
      ).toBeVisible();
      const downloadPath =
        await configurationPage.downloadCustomCodeCsvTemplate();
      await configurationPage.uploadCustomCodeCsv(downloadPath);
      const saveAllButton = page.getByRole('button', {
        name: 'Confirm & save codes',
      });
      const deleteAllButton = page.getByRole('button', {
        name: 'Undo & delete codes',
      });
      await expect(saveAllButton).toBeVisible();
      await expect(deleteAllButton).toBeVisible();

      await expect(
        page.getByText('Other Example', { exact: true })
      ).toBeVisible();
      await page.getByRole('searchbox', { name: 'Search codes' }).fill('oth');
      const editButton = page.getByRole('button', {
        name: 'Edit',
        exact: true,
      });
      const deleteButton = page.getByRole('button', {
        name: 'Delete',
        exact: true,
      });
      await expect(editButton).toBeVisible();
      await expect(deleteButton).toBeVisible();

      await editButton.click();
      await expect(
        page.getByRole('heading', { name: 'Edit 12345', level: 2 })
      ).toBeVisible();
      const testCode = 'test code ~';
      await page.getByLabel('Code #').fill(testCode);
      await page.getByLabel('Code system').selectOption('CVX');
      await page.getByLabel('Code name').fill('test code_name');
      await expect(
        page.getByRole('heading', { name: `Edit ${testCode}`, level: 2 })
      ).toBeVisible();
      await page.getByRole('button', { name: 'Save changes' }).click();

      await expect(
        page.getByText('Other Example', { exact: true })
      ).not.toBeVisible();
      await page.getByRole('searchbox', { name: 'Search codes' }).clear();
      await expect(page.getByText(testCode)).toBeVisible();

      const rows = page.locator('table tbody tr');
      const firstRow = rows.first();

      expect(await rows.all()).toHaveLength(3);
      await firstRow.getByRole('button', { name: 'Delete' }).click();
      await expect(page.getByText(testCode)).not.toBeVisible();
      expect(await rows.all()).toHaveLength(2);

      await page.getByRole('button', { name: 'Confirm & save codes' }).click();
      await expect(
        page.getByRole('heading', {
          name: 'Confirm & save codes?',
          exact: true,
          level: 2,
        })
      ).toBeVisible();
      await page.getByRole('button', { name: 'Yes, save codes' }).click();

      const savedCodeTableRows = page.locator('table tbody tr');
      await expect(
        savedCodeTableRows.getByText('ICD-10 Example')
      ).toBeVisible();
      await expect(savedCodeTableRows.getByText('LOINC Example')).toBeVisible();
    });

    await test.step('Activate modified draft', async () => {
      await configurationPage.goToActivateTab();
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
});
