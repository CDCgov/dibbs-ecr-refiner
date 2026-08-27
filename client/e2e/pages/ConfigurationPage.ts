import { Page, expect } from '@playwright/test';
import { uploadMonmothmaTestFile } from '../utils';

export class ConfigurationPage {
  constructor(private page: Page) {}

  async clearToasts() {
    await expect(this.page.locator('.Toastify__toast')).toHaveCount(0, {
      timeout: 10000,
    });
  }

  async uploadInlineTestEcrFile() {
    await uploadMonmothmaTestFile(this.page);
  }

  async goToCustomizeSectionsTab() {
    await this.page
      .getByRole('link', { name: 'Customize eICR sections', exact: true })
      .click();
    await this.checkHeading('Customize eICR sections');
  }

  async goToManageCodesTab() {
    await this.page
      .getByRole('link', { name: 'Manage codes', exact: true })
      .click();
    await this.checkHeading('Manage codes');
  }

  async goToTestTab() {
    await this.page
      .getByRole('link', { name: 'Test & export', exact: true })
      .click();
    await this.checkHeading('Test configuration');
  }

  private async checkHeading(text: string) {
    await expect(
      this.page.getByRole('heading', {
        name: text,
        level: 2,
      })
    ).toBeVisible();
  }

  async openCodeSetsDrawer() {
    await this.page
      .getByRole('button', { name: 'Condition code sets', exact: false })
      .click();
  }

  async searchForCodeSet(searchTerm: string, conditionName: string) {
    await this.page
      .getByRole('searchbox', { name: 'Search by condition name' })
      .fill(searchTerm);
    await this.page
      .getByRole('dialog')
      .getByRole('listitem')
      .filter({ hasText: conditionName })
      .hover();
  }

  async addCodeSet(searchTerm: string, conditionName: string) {
    await this.openCodeSetsDrawer();
    await this.searchForCodeSet(searchTerm, conditionName);
    await this.page.getByLabel(`Add ${conditionName}`).click();
    await this.page.getByRole('button', { name: 'Close drawer' }).click();
  }

  async deleteCodeSet(searchTerm: string, conditionName: string) {
    await this.openCodeSetsDrawer();
    await this.searchForCodeSet(searchTerm, conditionName);
    await this.page
      .getByRole('button', { name: `Remove ${conditionName}` })
      .click();
    await this.page.getByRole('button', { name: 'Close drawer' }).click();
  }

  async addCustomCode(code: string, codeSystem: string, codeName: string) {
    await this.page.getByRole('button', { name: 'Add custom code' }).click();
    const addSingleCodeButton = this.page.getByRole('button', {
      name: 'Add a single code',
    });
    await expect(addSingleCodeButton).toBeVisible();
    await addSingleCodeButton.click();
    await this.page.getByLabel('Code', { exact: true }).fill(code);
    await this.page
      .getByRole('combobox', { name: 'Code system' })
      .selectOption({ label: codeSystem });
    await this.page.getByLabel('Display name').fill(codeName);
    await this.page.getByRole('button', { name: 'Add custom code' }).click();
  }

  async editCustomCode(
    currentCodeName: string,
    {
      newCode,
      newCodeSystem,
      newCodeName,
    }: { newCode?: string; newCodeSystem?: string; newCodeName?: string } = {}
  ) {
    await this.page
      .getByRole('button', { name: `Edit custom code ${currentCodeName}` })
      .click();
    if (newCode)
      await this.page.getByLabel('Code', { exact: true }).fill(newCode);
    if (newCodeSystem)
      await this.page.getByLabel('Code system').selectOption(newCodeSystem);
    if (newCodeName)
      await this.page.getByLabel('Display name').fill(newCodeName);
  }

  async deleteCustomCode(codeName: string) {
    const table = this.page.getByRole('table');
    await expect(table).toBeVisible();
    const row = table.getByRole('row').filter({ hasText: codeName });
    await row.getByRole('button', { name: 'Delete custom code' }).click();
    await expect(this.page.getByText(codeName)).not.toBeVisible();
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
      .getByRole('button', { name: 'Activate this version' })
      .click();
    await this.page
      .getByRole('button', { name: 'Yes, turn on configuration' })
      .click();
  }
}
