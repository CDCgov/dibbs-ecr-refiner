import { test, expect } from './fixtures/fixtures';

test.describe('Viewing the application sign in content', () => {
  test('should be able to see the configuration page, and both testing and configuration tabs', async ({
    page,
    makeAxeBuilder,
  }) => {
    await expect(
      page.getByRole('link', { name: 'Provide Feedback' })
    ).toBeVisible();
    await expect(page.getByRole('link', { name: 'Testing' })).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Configurations', exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Configurations' })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    const menuButton = page.getByRole('button', {
      name: 'Open settings menu',
    });
    await expect(menuButton).toBeVisible();
    await menuButton.click();

    await expect(
      page.getByRole('menuitem', {
        name: 'Log out',
      })
    ).toBeVisible();
  });
});
