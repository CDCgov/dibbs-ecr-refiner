import { expect, Page } from '@playwright/test';

export class ConfigurationsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');
    await expect(
      this.page.getByRole('heading', {
        name: 'Configurations',
        exact: true,
        level: 1,
      })
    ).toBeVisible();
  }

  async createConfiguration(conditionName: string) {
    await this.page
      .getByRole('button', { name: 'Set up new configuration' })
      .click();
    await this.page.getByRole('combobox', { name: 'Select condition' }).click();
    await this.page
      .getByRole('combobox', { name: 'Select condition' })
      .fill(conditionName);
    await this.page.getByRole('option', { name: conditionName }).click();
    // NOTE: ComboboxOptions renders via a portal (see Combobox/index.tsx),
    // so it's a DOM sibling of the dialog, not a descendant. Selecting an
    // option starts its own ~100ms close transition independent of the
    // dialog. Wait for the listbox to fully close here, otherwise a
    // still-transitioning (semi-transparent) dropdown can linger in the
    // DOM and trip axe color-contrast checks in later steps.
    await expect(this.page.getByRole('listbox')).toBeHidden();
    await this.page
      .getByRole('button', { name: 'Set up configuration' })
      .click();
    await expect(this.page.getByRole('dialog')).toBeHidden();
  }

  async search(text: string) {
    await this.page
      .getByRole('searchbox', { name: 'Search configurations' })
      .fill(text);
  }

  async clearSearch() {
    await this.page
      .getByRole('searchbox', { name: 'Search configurations' })
      .clear();
  }
}
