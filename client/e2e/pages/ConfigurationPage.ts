import { Page, expect } from '@playwright/test';

export class ConfigurationPage {
  constructor(private page: Page) {}

  async clearToasts() {
    await expect(this.page.locator('.Toastify__toast')).toHaveCount(0, {
      timeout: 10000,
    });
  }

  async addCodeSet(searchTerm: string, conditionName: string) {
    await this.page
      .getByRole('button', { name: 'Add new code set to configuration' })
      .click();
    await this.page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .fill(searchTerm);
    await this.page
      .getByRole('listitem')
      .filter({ hasText: conditionName })
      .click();
    await this.page.getByRole('button', { name: 'Close drawer' }).click();
  }

  async deleteCodeSet(conditionName: string) {
    await this.clearToasts();
    await this.page
      .getByRole('button', {
        name: `View TES code set information for ${conditionName}`,
      })
      .hover();
    await this.page
      .getByRole('button', { name: `Delete code set ${conditionName}` })
      .click();
  }

  async addCustomCode(code: string, codeSystem: string, codeName: string) {
    await this.page
      .getByRole('button', { name: 'Add new custom code' })
      .click();
    await this.page.getByLabel('Code #').fill(code);
    await this.page.getByLabel('Code system').selectOption(codeSystem);
    await this.page.getByLabel('Code name').fill(codeName);
    await this.page.getByRole('button', { name: 'Add custom code' }).click();
  }

  async deleteCustomCode(code: string) {
    await this.page
      .getByRole('button', { name: `Delete custom code ${code}` })
      .click();
  }

  async downloadCustomCodeCsvTemplate(): Promise<string> {
    const downloadPromise = this.page.waitForEvent('download');
    await this.page.getByRole('button', { name: 'Download template' }).click();
    const download = await downloadPromise;

    const savePath = `/tmp/${download.suggestedFilename()}`;
    await download.saveAs(savePath);
    return savePath;
  }

  async uploadCustomCodeCsv(filePath: string) {
    await this.page.setInputFiles('input[type="file"]', filePath);
  }

  async activateConfiguration() {
    await this.page
      .getByRole('button', { name: 'Turn on configuration' })
      .click();
    await this.page
      .getByRole('button', { name: 'Yes, turn on configuration' })
      .click();
  }
}
