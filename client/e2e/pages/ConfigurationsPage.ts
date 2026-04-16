import { Page } from '@playwright/test';

export class ConfigurationsPage {
  constructor(private page: Page) {}

  async createConfiguration(conditionName: string) {
    await this.page
      .getByRole('button', { name: 'Set up new configuration' })
      .click();
    await this.page.getByRole('combobox', { name: 'Select condition' }).click();
    await this.page
      .getByRole('combobox', { name: 'Select condition' })
      .fill(conditionName);
    await this.page.getByRole('option', { name: conditionName }).click();
    await this.page
      .getByRole('button', { name: 'Set up configuration' })
      .click();
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
