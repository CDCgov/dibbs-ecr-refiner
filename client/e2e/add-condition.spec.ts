import { test, expect } from './fixtures/fixtures';
import { login, logout } from './utils';
import { CONFIGURATION_CTA } from '../src/pages/Configurations/utils';

test.describe
  .serial('Adding/modifying configurations by initial condition', () => {
  test.describe.configure({ retries: 1 });

  test.beforeAll(async ({ page }) => {
    await login(page);
  });

  test.afterAll(async ({ page }) => {
    await logout(page);
  });

  test('should be able to create a configuration for Acanthamoeba', async ({
    page,
    makeAxeBuilder,
  }) => {
    /// ==========================================================================
    /// Test that a new condition can be added
    /// ==========================================================================
    await page.getByRole('button', { name: CONFIGURATION_CTA }).click();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await page.getByTestId('combo-box-input').click();
    await page.getByTestId('combo-box-input').fill('Acanthamoeba');
    await page.getByTestId('combo-box-input').press('Tab');
    await page.getByRole('option', { name: 'Acanthamoeba' }).press('Enter');
    await page.getByTestId('combo-box-input').press('Tab');
    await page.getByTestId('combo-box-clear-button').press('Tab');
    await page.getByTestId('modalFooter').getByTestId('button').click();
    await expect(
      page.getByRole('heading', { name: 'New configuration created' })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    /// ==========================================================================
    /// Test that the drawer can open and add condition code sets
    /// ==========================================================================
    await page.getByRole('button', { name: 'Add new code set to' }).click();
    await expect(
      page.getByRole('heading', { name: 'Add condition code sets' })
    ).toBeVisible();

    // Add a few code sets and check that remove button shows up properly
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

    await page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .click();
    await page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .fill('disease');
    await page.getByText('Balamuthia mandrillaris Disease').click();
    await page.getByTestId('close-drawer').click();
    await page.waitForSelector(
      '[role="alert"]:has-text("Condition code set added")',
      { state: 'detached' }
    );

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(page.getByText('Status: Inactive')).toBeVisible();
    await expect(page.getByText('Editing: Version 1')).toBeVisible();

    await expect(
      page.getByRole('button', {
        name: 'Balamuthia mandrillaris Disease, 1178 codes in code set',
      })
    ).toBeVisible();

    /// ==========================================================================
    /// Test that custom codes work
    /// ==========================================================================
    await page.getByRole('button', { name: 'Custom codes' }).click();
    await page.getByRole('button', { name: 'Add new custom code' }).click();

    await page.getByRole('textbox', { name: 'Code #' }).click();
    await page.getByRole('textbox', { name: 'Code #' }).fill('1234');
    await page.getByTestId('Select').selectOption('rxnorm');
    await page.getByRole('textbox', { name: 'Code name' }).click();
    await page.getByRole('textbox', { name: 'Code name' }).fill('qwert');
    await page.getByTestId('modalFooter').getByTestId('button').click();
    await expect(
      page.getByRole('cell', { name: 'qwert', exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole('cell', { name: '1234', exact: true })
    ).toBeVisible();
    await page.getByText('Custom code added').click();

    /// ==========================================================================
    /// Test that section modification works as expected
    /// ==========================================================================
    await page.getByRole('button', { name: 'Sections' }).click();
    await expect(
      page.getByLabel('Include and refine section History of encounters')
    ).toBeChecked();

    const radio = page.getByLabel(
      'Include entire section History of encounters'
    );
    const parent = radio.locator('..');
    await parent.click();

    // Wait for saving to show up
    await page.getByText('Saving').waitFor({ state: 'visible' });

    // Wait for saving to go away (refetch finished)
    await page.getByText('Saving').waitFor({ state: 'detached' });

    await page.getByRole('button', { name: 'Acanthamoeba' }).click();

    await page.getByRole('button', { name: 'Sections' }).click();
    await expect(
      page.getByLabel('Include entire section History of encounters')
    ).toBeChecked();

    /// ==========================================================================
    /// Test that the condition and configuration creation shows up in the activity log
    /// ==========================================================================
    await page.getByText('Activity log').click();
    expect(page.getByRole('heading', { name: 'Activity log' }));

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({ hasText: 'Created configuration' })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({
          hasText: "Associated 'Balamuthia mandrillaris Disease' code set",
        })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({ hasText: "Added custom code '1234'" })
    ).toBeVisible();
  });

  /// ==========================================================================
  /// Test that a condition can be selected from configuration added in previous test
  /// ==========================================================================
  test('should be able to view configuration for Acanthamoeba', async ({
    page,
    makeAxeBuilder,
  }) => {
    await page
      .getByRole('row', {
        name: 'View inactive configuration for Acanthamoeba',
      })
      .click();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(
      page.getByRole('button', {
        name: 'Balamuthia mandrillaris Disease, 1178 codes in code set',
      })
    ).toBeVisible();
    await page
      .getByRole('button', {
        name: 'Balamuthia mandrillaris Disease, 1178 codes in code set',
      })
      .click();
    await expect(
      page.getByRole('heading', {
        name: 'Balamuthia mandrillaris Disease code set',
      })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(
      page.getByRole('button', { name: 'Custom codes 1' })
    ).toBeVisible();
  });

  test('should be able to delete condition Balamuthia mandrillaris from Acanthamoeba config', async ({
    page,
    makeAxeBuilder,
  }) => {
    /// ==========================================================================
    /// Test that a condition can be deleted from configuration added in previous test
    /// ==========================================================================
    await page
      .getByRole('row', {
        name: 'View inactive configuration for Acanthamoeba',
      })
      .click();

    // --- Locate the CONDITION CODE SETS container ---
    const conditionCodeSets = page.locator('div', {
      hasText: 'CONDITION CODE SETS',
    });

    // Locate the <li> row containing Balamuthia mandrillaris Disease delete button
    const balamuthiaRow = conditionCodeSets.locator('li', {
      has: page.getByRole('button', {
        name: 'Delete code set Balamuthia mandrillaris Disease',
      }),
    });

    // Hover over the row to reveal the delete button
    await balamuthiaRow.hover();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Click the delete button inside this row
    await balamuthiaRow
      .getByRole('button', {
        name: 'Delete code set Balamuthia mandrillaris Disease',
      })
      .click();

    const acanthamoebaButton = conditionCodeSets.getByRole('button', {
      name: /Acanthamoeba, \d+ codes in code set/,
    });

    await expect(acanthamoebaButton).toBeVisible();

    // User should see default code set once current code set has been deleted
    await expect(page.getByText('Acanthamoeba code set')).toBeVisible();

    // Expect "Balamuthia mandrillaris Disease" code set to no longer be visible
    const balamuthiaButton = conditionCodeSets.getByRole('button', {
      name: /Balamuthia mandrillaris Disease, \d+ codes in code set/,
    });
    await expect(balamuthiaButton).not.toBeVisible();

    /// ==========================================================================
    /// Test that the condition deletion shows up in the activity log
    /// ==========================================================================
    await page.getByText('Activity log').click();
    expect(page.getByRole('heading', { name: 'Activity log' }));

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({
          hasText: "Removed 'Balamuthia mandrillaris Disease' code set",
        })
    ).toBeVisible();
  });

  test('should be able export Acanthamoeba config', async ({ page }) => {
    /// ==========================================================================
    /// Test that a configuration can be exported
    /// ==========================================================================
    await page
      .getByRole('row', {
        name: 'View inactive configuration for Acanthamoeba',
      })
      .click();

    // Wait for the download event and trigger it
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('a[href*="/export"]').click(),
    ]);

    // Verify the file downloaded successfully
    const suggestedName = download.suggestedFilename();
    expect(suggestedName).toMatch(/Acanthamoeba_Code Export/);

    // Optionally, save it to a temp folder and verify it exists
    const path = await download.path();
    expect(path).toBeTruthy();
  });

  test('should be able edit and delete custom code', async ({
    page,
    makeAxeBuilder,
  }) => {
    /// ==========================================================================
    /// Test that custom codes can be edited and deleted
    /// ==========================================================================
    await page
      .getByRole('row', {
        name: 'View inactive configuration for Acanthamoeba',
      })
      .click();

    // Open the "Custom codes" section
    await page.locator('button', { hasText: 'Custom codes' }).click();

    // Click the Edit button for the existing custom code
    await page.getByText('Edit', { exact: true }).click();

    // Wait for the "Edit custom code" modal to appear
    const modal = page.locator('.usa-modal__main', {
      hasText: 'Edit custom code',
    });
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Edit the Code #
    const codeInput = modal.locator('input#code');
    await codeInput.fill('5678');

    // Change Code system to LOINC
    const systemSelect = modal.locator('select#system');
    await systemSelect.selectOption('loinc');

    // Change Code name to test-edit
    const nameInput = modal.locator('input#name');
    await nameInput.fill('test-edit');

    // Click the Update button
    const updateButton = modal.locator('button', { hasText: 'Update' });
    await updateButton.click();

    // Verify the row reflects updated values
    const updatedRow = page
      .locator('tbody tr')
      .filter({ hasText: '5678' })
      .filter({ hasText: 'LOINC' })
      .filter({ hasText: 'test-edit' });

    await expect(updatedRow).toBeVisible();

    // Verify that the old values are no longer present
    await expect(page.getByRole('cell', { name: '1234' })).not.toBeVisible();
    await expect(page.getByRole('cell', { name: 'qwert' })).not.toBeVisible();

    // Click the Delete button for the updated custom code
    await page
      .getByRole('button', { name: /Delete custom code test-edit/i })
      .click();

    // Verify the row is removed
    await expect(updatedRow).not.toBeVisible();

    // Verify that the "Custom codes" count updates to 0
    await expect(
      page.getByRole('button', { name: /Custom codes 0/i })
    ).toBeVisible();

    /// ==========================================================================
    /// Test that the custom code updates show up in the activity log
    /// ==========================================================================
    await page.getByText('Activity log').click();
    expect(page.getByRole('heading', { name: 'Activity log' }));

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({ hasText: "Updated custom code from '1234' to '5678'" })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({
          hasText:
            "Updated name for custom code '1234' from 'qwert' to 'test-edit'",
        })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({
          hasText:
            "Updated system for custom code '1234' from 'rxnorm' to 'loinc'",
        })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: 'Acanthamoeba' })
        .filter({ hasText: "Removed custom code '5678'" })
    ).toBeVisible();

    // filter by Acanthamoeba
    await page
      .getByLabel('Condition')
      .selectOption(
        'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/ceef5555-ce1a-42ff-a124-6508eec46658'
      );

    // should be 11 items on page 1 (including header)
    await expect(page.getByRole('row')).toHaveCount(11);
    await page.getByRole('button', { name: 'Next' }).click();

    // should be 3 items on page 2 (including header)
    await expect(page.getByRole('row')).toHaveCount(3);
  });
});
