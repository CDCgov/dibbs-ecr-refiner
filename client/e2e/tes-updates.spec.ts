import { expect, test } from './fixtures';

test.describe('TES updates page', () => {
  test.beforeEach(async ({ tesUpdatesPage }) => {
    await tesUpdatesPage.goto();
  });

  test('Page is accessible and has expected content', async ({
    makeAxeBuilder,
    tesUpdatesPage,
  }) => {
    await tesUpdatesPage.goToTesUpdate('5.0.0');
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await tesUpdatesPage.goToTesUpdate('6.0.0');
  });
});
