import { expect, Page } from '@playwright/test';

export class AppUpdatesPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');

    await this.page.getByLabel('Open settings menu').click();
    await this.page.getByRole('menuitem', { name: 'App updates' }).click();
    await expect(
      this.page.getByRole('heading', {
        name: 'App updates',
        exact: true,
        level: 1,
      })
    ).toBeVisible();
  }
}
