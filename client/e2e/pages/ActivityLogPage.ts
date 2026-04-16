import { Page, expect } from '@playwright/test';

type ActivityLogRow = {
  name: string;
  condition: string;
  action: string;
  date: string;
};

export class ActivityLogPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.getByRole('link', { name: 'Activity Log' }).click();
    await expect(
      this.page.getByRole('heading', {
        name: 'Activity log',
        exact: true,
        level: 1,
      })
    ).toBeVisible();
  }

  async selectConditionFromDropdown(conditionName: string) {
    await this.page
      .getByRole('combobox', { name: 'Condition' })
      .selectOption(conditionName);
  }

  async selectPage(page: number) {
    const button = this.page.getByRole('button', { name: `Page ${page}` });
    await expect(button).toBeVisible();
    await button.click();
    await expect(button).toHaveAttribute('aria-current', 'page');
  }

  async getTableRows(): Promise<ActivityLogRow[]> {
    return this.page.evaluate(() => {
      const headers = Array.from(
        document.querySelectorAll('table thead th')
      ).map((th) => th.textContent.trim());

      return Array.from(document.querySelectorAll('table tbody tr')).map(
        (row) =>
          Object.fromEntries(
            Array.from(row.querySelectorAll('td')).map((td, i) => [
              headers[i].toLowerCase(),
              td.textContent.trim(),
            ])
          )
      );
    }) as Promise<ActivityLogRow[]>;
  }
}
