import { deleteAllConfigurations } from './db';
import { test, expect } from './fixtures/fixtures';

test.describe('Activity log', () => {
  test.beforeEach(async ({ configurationsPage }) => {
    await configurationsPage.goto();
    await deleteAllConfigurations();
  });
  test.afterEach(async () => {
    await deleteAllConfigurations();
  });

  test('Check empty state', async ({ activityLogPage }) => {
    await activityLogPage.goto();
    const rowData = await activityLogPage.getTableRows();
    expect(rowData).toHaveLength(0);
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
  });
});
