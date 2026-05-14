import { Locator, Page, expect } from '@playwright/test';
import { uploadMonmothmaTestFile } from '../utils';

export class TestingPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.getByRole('link', { name: 'Testing', exact: true }).click();
    await expect(
      this.page.getByRole('heading', { name: 'Test Refiner', exact: true })
    ).toBeVisible();
  }

  getConditionCheckbox(conditionName: string): Locator {
    return this.page.getByRole('checkbox', {
      name: `Use ${conditionName} configuration in refinement process`,
    });
  }

  getConditionSelect(conditionName: string): Locator {
    return this.page.getByRole('combobox', { name: conditionName });
  }

  async uploadTestFile() {
    await uploadMonmothmaTestFile(this.page);
  }

  async runRefinement() {
    await this.page.getByRole('button', { name: 'Refine eCR' }).click();
  }

  async startOver() {
    await this.page.getByRole('button', { name: 'Start over' }).click();
  }
}
