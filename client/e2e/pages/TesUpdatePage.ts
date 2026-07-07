import { expect, Page } from '@playwright/test';

export class TesUpdatePage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');

    await this.page.getByLabel('Open settings menu').click();
    await this.page.getByRole('menuitem', { name: 'TES updates' }).click();
    await expect(
      this.page.getByRole('heading', {
        name: 'TES Updates',
        exact: true,
        level: 1,
      })
    ).toBeVisible();
  }

  async goToTesUpdate(version: number) {
    await this.page
      .getByRole('button', { name: `Version ${version}.0.0` })
      .click();

    expect(
      this.page.getByText(`What's changed in Version ${version}.0.0`)
    ).toBeDefined();
  }
}
