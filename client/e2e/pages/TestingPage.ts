import { Page, expect } from '@playwright/test';
import { uploadMonmothmaTestFile } from '../utils';

export class TestingPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.getByRole('link', { name: 'Testing', exact: true }).click();
    await expect(
      this.page.getByRole('heading', { name: 'Test Refiner', exact: true })
    ).toBeVisible();
  }

  async uploadTestFile() {
    await uploadMonmothmaTestFile(this.page);
  }

  async startOver() {
    await this.page.getByRole('button', { name: 'Start over' }).click();
  }
}
