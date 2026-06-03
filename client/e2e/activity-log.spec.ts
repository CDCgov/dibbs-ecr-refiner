import { deleteAllConfigurations } from './db';
import { test, expect } from './fixtures';

test.describe('Activity log', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await deleteAllConfigurations();
    await configurationsPage.goto();
  });
  test.afterEach(async () => {
    await deleteAllConfigurations();
  });

  test('Check empty state', async ({ activityLogPage, page }) => {
    await activityLogPage.goto();

    await expect(page.getByLabel('Condition').getByRole('option')).toHaveText([
      'All conditions',
    ]);

    const rowData = await activityLogPage.getTableRows();
    expect(rowData).toHaveLength(0);
    await expect(
      page.getByRole('navigation', { name: 'Pagination' }).getByRole('button')
    ).toHaveCount(1);
  });

  test('Check that condition filters are sorted alphabetically by name', async ({
    activityLogPage,
    api,
    page,
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
  });

  test('Check entries from configuration creation', async ({
    activityLogPage,
    api,
  }) => {
    const conditionOne = 'COVID-19';
    const conditionTwo = 'Zika Virus Disease';
    await api.createConfiguration(conditionOne);
    await api.createConfiguration(conditionTwo);
    await activityLogPage.goto();
    const rowData = await activityLogPage.getTableRows();
    expect(rowData).toHaveLength(2);

    const expectedAction = 'Created configuration';
    const rowOne = rowData.find((r) => r.condition.includes(conditionOne));
    expect(rowOne).toBeTruthy();

    const rowTwo = rowData.find((r) => r.condition.includes(conditionTwo));
    expect(rowTwo).toBeTruthy();

    expect(rowOne?.action).toBe(expectedAction);
    expect(rowTwo?.action).toBe(expectedAction);

    await activityLogPage.selectConditionFromDropdown(conditionOne);
    const conditionOneOnlyRows = await activityLogPage.getTableRows();
    expect(conditionOneOnlyRows).toHaveLength(1);
  });

  test('Check individual custom code entries from CSV upload', async ({
    page,
    api,
    activityLogPage,
  }) => {
    const condition = 'Lead in Blood';
    const config = await api.createConfiguration(condition);

    // Create 50 codes to upload
    const systems = ['loinc', 'icd10', 'snomed', 'rxnorm', 'cvx', 'other'];
    const systemNames = ['LOINC', 'ICD-10', 'SNOMED', 'RxNorm', 'CVX', 'Other'];
    const customCodes = Array.from({ length: 50 }, (_, i) => ({
      code: `mc-${i + 1}`,
      name: `mock code ${i + 1}`,
      system_key: systems[i % systems.length],
      system_display_name: systemNames[i % systems.length],
    }));

    await api.uploadCustomCodeCsv(config.id, customCodes);
    await activityLogPage.goto();
    const rowData = await activityLogPage.getTableRows();

    const expectedAction = `Added ${customCodes.length} custom codes from CSV`;
    const expectedRow = rowData.find((r) => r.action.includes(expectedAction));
    expect(expectedRow?.action).toContain(expectedAction);

    const modalButton = page.getByRole('button', { name: 'View all' });
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
      page.getByText(customCodes[1].name, { exact: true })
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
  });
});
