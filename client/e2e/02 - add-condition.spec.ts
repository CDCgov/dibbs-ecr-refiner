import { test, expect } from './fixtures/fixtures';
import { readFile } from 'node:fs/promises';

test.describe('Adding/modifying configurations by initial condition', () => {
  test('should be able to create a configuration', async ({
    page,
    makeAxeBuilder,
    configurationPage,
  }) => {
    const configurationToTest = configurationPage.getConfigurationName();

    // start on the activate page for the configuration
    await expect(
      page.getByRole('heading', { name: configurationToTest, exact: true })
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
    await page.getByRole('listitem').filter({ hasText: 'Diphtheria' }).click();
    await expect(
      page.getByRole('button', { name: 'Remove Diphtheria' })
    ).toBeVisible();

    await page
      .getByRole('listitem')
      .filter({ hasText: 'Diphyllobothriasis' })
      .click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Diphyllobothriasis',
      })
    ).toBeVisible();

    await page
      .getByRole('listitem')
      .filter({ hasText: 'Double Outlet Right Ventricle (DORV)' })
      .click();
    await expect(
      page.getByRole('button', {
        name: 'Remove Double Outlet Right Ventricle (DORV)',
      })
    ).toBeVisible();

    await page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .click();
    await page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .fill('syndrome');
    await page.getByText('Down Syndrome').click();
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
        name: 'View TES code set information for Down Syndrome',
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
    /// Test that CSV upload for custom codes works
    /// ==========================================================================
    await page.getByRole('button', { name: 'Import from CSV' }).click();
    await expect(
      page.getByRole('heading', { name: 'Import from CSV' })
    ).toBeVisible();

    await expect(
      page.getByRole('heading', { name: 'Import from CSV' })
    ).toBeVisible();

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: 'Download template' }).click(),
    ]);

    expect(download.suggestedFilename()).toBe(
      'custom_code_upload_template.csv'
    );

    const path = await download.path();
    if (!path) throw new Error('Download path was null');
    const contents = await readFile(path, 'utf-8');

    expect(contents).toBe(
      `code_number,code_system,display_name
[CODE_NUMBER],[CODE_SYSTEM],[DISPLAY_NAME]
`
    );

    const csv = `code_number,code_system,display_name
10001,LOINC,TEST 1
10002,LOINC,TEST 2
`;

    const importPanel = page.locator('div', {
      has: page.getByRole('heading', { name: 'Import from CSV' }),
    });
    const fileInput = importPanel.locator('input[type="file"]');

    const [uploadResponse] = await Promise.all([
      page.waitForResponse(
        (resp) =>
          resp.request().method() === 'POST' &&
          resp.url().includes('/custom-codes/upload')
      ),
      fileInput.setInputFiles({
        name: 'custom_codes.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csv),
      }),
    ]);

    expect(uploadResponse.ok(), 'upload POST returned non-2xx').toBeTruthy();

    await expect(
      page.getByRole('heading', { name: 'Custom codes' })
    ).toBeVisible();

    await expect(
      page.getByRole('cell', { name: 'TEST 1', exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole('cell', { name: '10001', exact: true })
    ).toBeVisible();

    await expect(
      page.getByRole('cell', { name: 'TEST 2', exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole('cell', { name: '10002', exact: true })
    ).toBeVisible();

    /// ==========================================================================
    /// Test that section modification works as expected
    /// ==========================================================================
    await page.getByRole('button', { name: 'Sections' }).click();

    const latestSpecRowCount = 21; // spec: 3.1.1, including skipped sections
    await expect(page.locator('table tbody tr')).toHaveCount(
      latestSpecRowCount
    );

    // This is the default setting for the skipped sections (see specification.py)
    await expect(page.getByText('Preserve & retain all data')).toHaveCount(2);

    // Check that a couple of expected options are visible
    await expect(
      page.getByRole('cell', {
        name: 'Reason For Visit',
        exact: true,
      })
    ).toBeVisible();

    await expect(
      page.getByRole('cell', {
        name: 'Medications',
        exact: true,
      })
    ).toBeVisible();

    await expect(
      page.getByLabel('Include Encounters section rules in refined document.')
    ).toBeChecked();

    // click the switch to toggle it
    await page
      .getByRole('switch', { name: 'Refine & optimize Encounters section' })
      .click();

    // Wait for saving to show up
    await page.getByText('Saving').waitFor({ state: 'visible' });

    // Wait for saving to go away (refetch finished)
    await page.getByText('Saving').waitFor({ state: 'detached' });
    await page.getByText('Saved').waitFor({ state: 'visible' });

    await page.getByRole('button', { name: configurationToTest }).click();

    await page.getByRole('button', { name: 'Sections' }).click();

    await expect(
      page.getByLabel('Include Encounters section rules in refined document.')
    ).toBeChecked();

    // switch was previously toggled off which adds one more to the total count
    await expect(page.getByText('Preserve & retain all data')).toHaveCount(3);

    /// ==========================================================================
    /// Test that the condition and configuration creation shows up in the activity log
    /// ==========================================================================
    await page.getByText('Activity log').click();
    expect(page.getByRole('heading', { name: 'Activity log' }));

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // filter by the created configuration
    await page
      .getByLabel('Condition')
      .selectOption({ label: configurationToTest });

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({ hasText: 'Created configuration' })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({
          hasText: "Associated 'Down Syndrome' code set",
        })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({ hasText: "Added custom code '1234'" })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({ hasText: 'Added 2 custom codes' })
    ).toBeVisible();
  });

  /// ==========================================================================
  /// Test that a condition can be selected from configuration added in previous test
  /// ==========================================================================
  test('should be able to view configuration', async ({
    page,
    makeAxeBuilder,
    configurationPage,
  }) => {
    const configurationToTest = configurationPage.getConfigurationName();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await page
      .getByRole('link', { name: 'Configurations', exact: true })
      .click();
    await page.getByTestId('table').getByText(configurationToTest).click();
    await expect(
      page.getByRole('heading', { name: configurationToTest, exact: true })
    ).toBeVisible();

    await page.getByRole('button', { name: 'Add new code set to' }).click();
    await expect(
      page.getByRole('heading', { name: 'Add condition code sets' })
    ).toBeVisible();

    await page
      .getByRole('listitem')
      .filter({ hasText: 'Down Syndrome' })
      .click();

    await page.getByRole('listitem').filter({ hasText: 'Diphtheria' }).click();

    await page
      .getByRole('listitem')
      .filter({ hasText: 'Diphyllobothriasis' })
      .click();
    await page
      .getByRole('listitem')
      .filter({ hasText: 'Double Outlet Right Ventricle (DORV)' })
      .click();

    await page.getByTestId('close-drawer').click();

    // Wait for prior notifications to clear
    await page.waitForSelector('[role="alert"]', { state: 'detached' });

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

    // click away and navigate back
    await page
      .getByRole('link', { name: 'Configurations', exact: true })
      .click();
    await page
      .getByRole('heading', {
        name: 'Configurations',
      })
      .click();
    await page.getByTestId('table').getByText(configurationToTest).click();

    await expect(
      page.getByRole('button', {
        name: 'View TES code set information for Down Syndrome',
      })
    ).toBeVisible();
    await page
      .getByRole('button', {
        name: 'View TES code set information for Down Syndrome',
      })
      .click();
    await expect(
      page.getByRole('heading', {
        name: 'Down Syndrome code set',
      })
    ).toBeVisible();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(
      page.getByRole('button', { name: 'Custom codes 1' })
    ).toBeVisible();

    // --- Locate the CONDITION CODE SETS container ---
    const conditionCodeSets = page.locator('div', {
      hasText: 'CONDITION CODE SETS',
    });

    // Locate the <li> row containing Down Syndrome delete button
    const downSyndromeRow = conditionCodeSets.locator('li', {
      has: page.getByRole('button', {
        name: 'Delete code set Down Syndrome',
      }),
    });

    // Hover over the row to reveal the delete button
    await downSyndromeRow.hover();

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    // Click the delete button inside this row
    await downSyndromeRow
      .getByRole('button', {
        name: 'Delete code set Down Syndrome',
      })
      .click();

    const defaultCodeSetButton = conditionCodeSets.getByRole('button', {
      name: `View TES code set information for ${configurationToTest}`,
    });

    await expect(defaultCodeSetButton).toBeVisible();

    // User should see default code set once current code set has been deleted
    await expect(
      page.getByRole('button', {
        name: `View TES code set information for ${configurationToTest}`,
      })
    ).toBeVisible();

    // Expect "Down Syndrome" code set to no longer be visible
    const downSyndromeButton = conditionCodeSets.getByRole('button', {
      name: /Down Syndrome, \d+ codes in code set/,
    });
    await expect(downSyndromeButton).not.toBeVisible();

    /// ==========================================================================
    /// Test that the condition deletion shows up in the activity log
    /// ==========================================================================
    await page.getByText('Activity log').click();
    expect(page.getByRole('heading', { name: 'Activity log' }));

    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await page
      .getByLabel('Condition')
      .selectOption({ label: configurationToTest });

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({
          hasText: "Removed 'Down Syndrome' code set",
        })
    ).toBeVisible();

    await page
      .getByRole('link', { name: 'Configurations', exact: true })
      .click();
    await page
      .getByRole('button', {
        name: `Configure the configuration for ${configurationToTest} `,
      })
      .filter({ hasText: configurationToTest })
      .click();

    // Open the "Custom codes" section
    await page.getByText('Custom codes').click();

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
        .filter({ hasText: configurationToTest })
        .filter({ hasText: "Updated custom code from '1234' to '5678'" })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({
          hasText:
            "Updated name for custom code '1234' from 'qwert' to 'test-edit'",
        })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({
          hasText:
            "Updated system for custom code '1234' from 'rxnorm' to 'loinc'",
        })
    ).toBeVisible();

    await expect(
      page
        .getByRole('row')
        .filter({ hasText: 'refiner' })
        .filter({ hasText: configurationToTest })
        .filter({ hasText: "Removed custom code '5678'" })
    ).toBeVisible();

    // filter by the created configuration
    await page
      .getByLabel('Condition')
      .selectOption({ label: configurationToTest });

    // should be 11 items on page 1 (including header)
    await expect(page.getByRole('row')).toHaveCount(11);
    await page.getByRole('button', { name: 'Next' }).click();

    // should be 2 items on page 2 (including header)
    await expect(page.getByRole('row')).toHaveCount(2);
  });

  test('should be able export the created config', async ({
    page,
    configurationPage,
  }) => {
    const configurationToTest = configurationPage.getConfigurationName();

    // start on the activate page for the configuration
    await expect(
      page.getByRole('heading', { name: configurationToTest, exact: true })
    ).toBeVisible();

    // Wait for the download event and trigger it
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('a[href*="/export"]').click(),
    ]);

    // Verify the file downloaded successfully
    const suggestedName = download.suggestedFilename();
    expect(suggestedName).toContain(
      `${configurationToTest.replace(/ /g, '_')}_Code Export`
    );

    // Optionally, save it to a temp folder and verify it exists
    const path = await download.path();
    expect(path).toBeTruthy();
  });
});
