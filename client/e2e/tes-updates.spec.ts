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
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await tesUpdatesPage.goToTesUpdate('6.0.0');

    const firstRowVersion6 = page.getByRole('row').first();
    expect(firstRowVersion6.getByText('Acanthamoeba')).toBeDefined();
    // since the numbers for the diff are checked in the integration test in
    // a fixed diff environment, we'll just check that numbers get rendered here
    expect(firstRowVersion6.getByText(/\d+ added, \d+ removed/)).toBeDefined();

    const lastRowVersion6 = page.getByRole('row').last();
    expect(lastRowVersion6.getByText('Zika Virus Disease')).toBeDefined();
    expect(lastRowVersion6.getByText(/\d+ added, \d+ removed/)).toBeDefined();
  });
});
