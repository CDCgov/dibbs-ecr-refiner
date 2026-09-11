import { LATEST_TES_VERSION, PREVIOUS_TES_VERSION } from './constants';
import { clearDb, makeOldTesVersionConfiguration } from './db';
import { expect, test } from './fixtures';

test.describe('TES updates page', () => {
  test.beforeEach(async ({ tesUpdatesPage }) => {
    await clearDb();
    await tesUpdatesPage.goto();
  });
  test.afterEach(async () => {
    await clearDb();
  });

  test('Page is accessible and has expected content', async ({
    makeAxeBuilder,
    tesUpdatesPage,
    page,
  }) => {
    await tesUpdatesPage.goToTesUpdate(PREVIOUS_TES_VERSION);
    const firstRowPreviousVersion = page.getByRole('row').first();
    expect(firstRowPreviousVersion.getByText('Acanthamoeba')).toBeDefined();
    // since the numbers for the diff are checked in the integration test in
    // a fixed diff environment, we'll just check that numbers get rendered here
    expect(
      firstRowPreviousVersion.getByText(/\d+ added, \d+ removed/)
    ).toBeDefined();
    const firstRowDownloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Export as CSV' }).first().click();
    const acanthomebaDownload = await firstRowDownloadPromise;

    expect(acanthomebaDownload.suggestedFilename()).toMatch(
      new RegExp(
        `Acanthamoeba_TES_v${PREVIOUS_TES_VERSION}_change_summary.csv$`
      )
    );
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await tesUpdatesPage.goToTesUpdate(LATEST_TES_VERSION);

    const lastRowLatestVersion = page.getByRole('row').last();
    expect(lastRowLatestVersion.getByText('Zika Virus Disease')).toBeDefined();
    expect(
      lastRowLatestVersion.getByText(/\d+ added, \d+ removed/)
    ).toBeDefined();
    const lastRowDownloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Export as CSV' }).last().click();
    const zikaDownload = await lastRowDownloadPromise;

    expect(zikaDownload.suggestedFilename()).toMatch(
      new RegExp(
        `Zika-Virus-Disease_TES_v${LATEST_TES_VERSION}_change_summary.csv$`
      )
    );
  });

  test('View updates renders drafts that need to be updated', async ({
    makeAxeBuilder,
    tesUpdatesPage,
    page,
  }) => {
    await makeOldTesVersionConfiguration('Cysticercosis', 'draft');
    await makeOldTesVersionConfiguration('Diphyllobothriasis', 'active');

    await tesUpdatesPage.goToUpdateActionsPage();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    const updateTable = page.getByRole('table', {
      name: 'Update existing drafts',
    });

    await expect(
      updateTable.getByRole('cell', { name: 'Cysticercosis', exact: true })
    ).toBeVisible();
    await expect(updateTable.getByText('Diphyllobothriasis')).toBeHidden();

    const createTable = page.getByRole('table', {
      name: 'Create Draft To Update',
    });

    await expect(
      createTable.getByRole('cell', { name: 'Diphyllobothriasis', exact: true })
    ).toBeVisible();
    await expect(createTable.getByText('Cysticercosis')).toBeHidden();
  });

  test('Applying TES updates for an active configuration logs an activity log entry', async ({
    tesUpdatesPage,
    activityLogPage,
    page,
  }) => {
    await makeOldTesVersionConfiguration('Cysticercosis', 'active');

    await tesUpdatesPage.goToUpdateActionsPage();

    await tesUpdatesPage.selectActiveConfigurationForUpdate('Cysticercosis');
    await tesUpdatesPage.applyUpdates();
    await tesUpdatesPage.confirmApplyUpdates();

    await expect(
      page.getByRole('heading', {
        name: 'Configurations have been updated',
        exact: true,
      })
    ).toBeVisible();

    await activityLogPage.goto();

    const rows = await activityLogPage.getTableRows();
    expect(
      rows.some((r) =>
        r.action.includes(
          'Created draft from active configuration with TES updates'
        )
      )
    ).toBe(true);
  });
});
