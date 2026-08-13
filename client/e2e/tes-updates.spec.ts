import { expect, test } from './fixtures';

test.describe('TES updates page', () => {
  test.beforeEach(async ({ tesUpdatesPage }) => {
    await tesUpdatesPage.goto();
  });

  test('Page is accessible and has expected content', async ({
    makeAxeBuilder,
    tesUpdatesPage,
    page,
  }) => {
    await tesUpdatesPage.goToTesUpdate('5.0.0');
    const firstRowVersion5 = page.getByRole('row').first();
    expect(firstRowVersion5.getByText('Acanthamoeba')).toBeDefined();
    // since the numbers for the diff are checked in the integration test in
    // a fixed diff environment, we'll just check that numbers get rendered here
    expect(firstRowVersion5.getByText(/\d+ added, \d+ removed/)).toBeDefined();
    const firstRowDownloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Export as CSV' }).first().click();
    const acanthomebaDownload = await firstRowDownloadPromise;

    expect(acanthomebaDownload.suggestedFilename()).toMatch(
      /Acanthamoeba_TES_v5.0.0_change_summary.csv$/
    );
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await tesUpdatesPage.goToTesUpdate('6.0.0');

    const lastRowVersion6 = page.getByRole('row').last();
    expect(lastRowVersion6.getByText('Zika Virus Disease')).toBeDefined();
    expect(lastRowVersion6.getByText(/\d+ added, \d+ removed/)).toBeDefined();
    const lastRowDownloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Export as CSV' }).last().click();
    const zikaDownload = await lastRowDownloadPromise;

    expect(zikaDownload.suggestedFilename()).toMatch(
      /Zika-Virus-Disease_TES_v6.0.0_change_summary.csv$/
    );
  });
});
