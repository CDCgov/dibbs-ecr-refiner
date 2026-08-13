import { expect, Page } from '@playwright/test';

export class AppUpdatesPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');

    const settingsMenu = this.page.getByLabel('Open settings menu');
    await settingsMenu.waitFor({ state: 'visible' });
    await settingsMenu.click();

    const appUpdatesItem = this.page.getByRole('menuitem', {
      name: 'App updates',
    });
    await appUpdatesItem.waitFor({ state: 'visible' });
    await appUpdatesItem.click();
    await expect(
      this.page.getByRole('heading', {
        name: 'App updates',
        exact: true,
        level: 1,
      })
    ).toBeVisible();
  }
}
