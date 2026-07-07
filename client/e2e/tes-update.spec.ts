import { expect, test } from './fixtures';

test.describe('TES updates page', () => {
  test.beforeEach(async ({ tesUpdatePage }) => {
    await tesUpdatePage.goto();
  });

  test('Page is accessible and has expected content', async ({
    makeAxeBuilder,
    tesUpdatePage,
  }) => {
    await tesUpdatePage.goToTesUpdate(3);
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await tesUpdatePage.goToTesUpdate(6);
  });
});
