import { Page } from '@playwright/test';
import { expect } from '../fixtures';

export class ManageCodesPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page
      .getByRole('link', { name: 'Manage codes', exact: true })
      .click();
    await expect(
      this.page.getByRole('heading', { name: 'Manage codes', exact: true })
    ).toBeVisible();
  }

  async deleteAllVisibleCustomCodes() {
    const table = this.page.getByRole('table');
    await expect(table).toBeVisible();

    const selectAllCheckbox = table.getByRole('checkbox', {
      name: 'Include all codes in bulk operation',
    });
    await selectAllCheckbox.click();
    await expect(selectAllCheckbox).toBeChecked();

    const controlPanel = this.page.getByTestId('control-panel');
    await expect(controlPanel).toBeVisible();
    await controlPanel.getByRole('button', { name: 'More options' }).click();

    const customCodeDeletionButton = this.page.getByText(
      /^Delete \d+ custom codes?$/
    );
    await expect(customCodeDeletionButton).toBeVisible();
    await customCodeDeletionButton.click();

    await expect(
      this.page.getByText(/^\d+ custom codes? will be deleted$/)
    ).toBeVisible();
    const deleteButton = this.page.getByRole('button', {
      name: /^Delete \d+ codes?$/,
    });
    await expect(deleteButton).toBeVisible();
    await deleteButton.click();
    await expect(controlPanel).not.toBeVisible();
  }
}
