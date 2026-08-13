import { clearDb } from './db';
import { test, expect } from './fixtures';

test.describe('Activity log', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await clearDb();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
  });

  test('Check empty state', async ({
    activityLogPage,
    page,
    makeAxeBuilder,
  }) => {
    await activityLogPage.goto();

    await expect(page.getByLabel('Condition').getByRole('option')).toHaveText([
      'All conditions',
    ]);

    const rowData = await activityLogPage.getTableRows();
    expect(rowData).toHaveLength(0);
    await expect(
      page.getByRole('navigation', { name: 'Pagination' }).getByRole('button')
    ).toHaveCount(1);
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Check that condition filters are sorted alphabetically by name', async ({
    activityLogPage,
    api,
    page,
    makeAxeBuilder,
  }) => {
    const conditionOne = 'Coal Workers’ Pneumoconiosis (CWP)';
    const conditionTwo = 'COVID-19';
    const conditionThree = 'Zika Virus Disease';
    await api.createConfiguration(conditionOne);
    await api.createConfiguration(conditionTwo);
    await api.createConfiguration(conditionThree);
    await activityLogPage.goto();

    await expect(page.getByLabel('Condition').getByRole('option')).toHaveText([
      'All conditions',
      conditionOne,
      conditionTwo,
      conditionThree,
    ]);
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Check entries from configuration creation', async ({
    activityLogPage,
    api,
    makeAxeBuilder,
  }) => {
    const conditionOne = 'COVID-19';
    const conditionTwo = 'Zika Virus Disease';

    await api.createConfiguration(conditionOne);
    await api.createConfiguration(conditionTwo);

    await activityLogPage.goto();

    const rowData = await activityLogPage.getTableRows();

    // Each version 1 configuration creates:
    // 1. Created configuration
    // 2. Added '<Condition>' code set
    expect(rowData).toHaveLength(4);

    const conditionOneRows = rowData.filter((r) =>
      r.condition.includes(conditionOne)
    );
    const conditionTwoRows = rowData.filter((r) =>
      r.condition.includes(conditionTwo)
    );

    expect(conditionOneRows).toHaveLength(2);
    expect(conditionTwoRows).toHaveLength(2);

    expect(
      conditionOneRows.some((r) => r.action === 'Created configuration')
    ).toBe(true);
    expect(
      conditionOneRows.some((r) =>
        r.action.includes(`Added '${conditionOne}' code set`)
      )
    ).toBe(true);

    expect(
      conditionTwoRows.some((r) => r.action === 'Created configuration')
    ).toBe(true);
    expect(
      conditionTwoRows.some((r) =>
        r.action.includes(`Added '${conditionTwo}' code set`)
      )
    ).toBe(true);

    await activityLogPage.selectConditionFromDropdown(conditionOne);

    const conditionOneOnlyRows = await activityLogPage.getTableRows();

    expect(conditionOneOnlyRows).toHaveLength(2);

    expect(
      conditionOneOnlyRows.some((r) => r.action === 'Created configuration')
    ).toBe(true);
    expect(
      conditionOneOnlyRows.some((r) =>
        r.action.includes(`Added '${conditionOne}' code set`)
      )
    ).toBe(true);

    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Check individual custom code entries from CSV upload', async ({
    page,
    api,
    activityLogPage,
    makeAxeBuilder,
  }) => {
    const condition = 'Lead in Blood';
    const config = await api.createConfiguration(condition);

    // Create 50 codes to upload
    const systems = await api.getSystems();
    const customCodes = Array.from({ length: 50 }, (_, i) => ({
      code: `mc-${i + 1}`,
      display: `mock code ${i + 1}`,
      system_id: systems[i % systems.length].id,
    }));

    await api.uploadCustomCodeCsv(config.id, customCodes);
    await activityLogPage.goto();
    const rowData = await activityLogPage.getTableRows();

    const expectedAction = `Added ${customCodes.length} custom codes from CSV`;
    const expectedRow = rowData.find((r) => r.action.includes(expectedAction));
    expect(expectedRow?.action).toContain(expectedAction);

    const modalButton = page.getByRole('button', { name: 'View all' });
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await expect(modalButton).toBeVisible();
    await expect(modalButton).toBeEnabled();
    await modalButton.click();

    await expect(
      page.getByRole('heading', { name: 'Custom codes', level: 2 })
    ).toBeVisible();
    await expect(page.getByText('Imported by refiner on')).toBeVisible();
    await expect(page.getByRole('table').getByRole('row')).toHaveCount(
      customCodes.length + 1 // including header row
    );
    await expect(
      page.getByText(customCodes[1].display, { exact: true })
    ).toBeInViewport();

    // We shouldn't be able to see the last row until we scroll
    const lastRow = page.getByRole('table').getByRole('row').last();
    await expect(lastRow).not.toBeInViewport();

    // Scroll and check again
    await lastRow.scrollIntoViewIfNeeded();
    await expect(lastRow).toBeInViewport();

    await page.getByRole('button', { name: 'Close this window' }).click();
    await expect(
      page.getByRole('heading', { name: 'Activity log' })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
  });

  test('Export button downloads a CSV file', async ({
    page,
    activityLogPage,
  }) => {
    await activityLogPage.goto();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Export as CSV' }).click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(
      /^Activity_Log_Export_\d{6}_\d{2}_\d{2}_\d{2}\.csv$/
    );
  });

  test('Code set Export as CSV link downloads the added code set', async ({
    page,
    activityLogPage,
    api,
  }) => {
    const condition = 'COVID-19';

    await api.createConfiguration(condition);
    await activityLogPage.goto();

    const codeSetRow = page
      .getByRole('row')
      .filter({ hasText: `Added '${condition}' code set` });

    await expect(codeSetRow).toBeVisible();

    const exportLink = codeSetRow.getByRole('link', {
      name: 'Export as CSV',
    });

    await expect(exportLink).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await exportLink.click();

    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(
      /^COVID-19_code_set_added_\d{6}_\d{2}_\d{2}_\d{2}\.csv$/
    );
  });
});
