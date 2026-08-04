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
    expect(firstRowVersion6.getByText(/\d+ added, \d+ removed/)).toBeDefined();

    const lastRowVersion6 = page.getByRole('row').last();
    expect(lastRowVersion6.getByText('Zika Virus Disease')).toBeDefined();
    expect(lastRowVersion6.getByText(/\d+ added, \d+ removed/)).toBeDefined();
  });
});
