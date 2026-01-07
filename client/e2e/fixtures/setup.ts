import { test as baseTest, expect, Page, WorkerInfo } from '@playwright/test';
import { deleteConfigurationArtifacts, login } from '../utils';
class ConfigurationPage {
  private readonly conditionIndex: number;
  private conditionName: string = '';

  constructor(
    public readonly page: Page,
    conditionIndex: number
  ) {
    this.conditionIndex = conditionIndex;
  }

  async createNewConfiguration(page: Page) {
    await this.page.goto('/configurations');
    await page
      .getByRole('button', { name: 'Set up new configuration' })
      .click();
    await page.getByTestId('combo-box-input').click();

    await page.getByRole('option').nth(this.conditionIndex).click();

    await page.keyboard.press('Enter');
    const createdConfigurationName = await page
      .getByTestId('combo-box-input')
      .inputValue();

    this.conditionName = createdConfigurationName;

    await page.getByRole('button', { name: 'Set up configuration' }).click();

    await expect(
      page.locator(
        `h4:has-text("New configuration created") + p:has-text("${createdConfigurationName}")`
      )
    ).toBeVisible();
  }

  getConfigurationName() {
    return this.conditionName;
  }
}

const defaultFixturesTest = baseTest.extend<object>({
  page: async ({ page }, use) => {
    // start in the logged in homepage
    await page.goto('/configurations');
    const returnToHomepageButton = page.getByRole('button', {
      name: 'Return to homepage',
    });
    if (returnToHomepageButton) {
      await login(page, 'http://localhost:8081');
    }
    await use(page);
  },
});

type RefinerFixtures = {
  configurationPage: ConfigurationPage;
};
export const test = defaultFixturesTest.extend<RefinerFixtures>({
  configurationPage: async ({ page }, use, workerInfo: WorkerInfo) => {
    const configurationPage = new ConfigurationPage(
      page,
      workerInfo.workerIndex
    );
    if (configurationPage.getConfigurationName() === '') {
      await configurationPage.createNewConfiguration(page);
    }
    await use(configurationPage);

    // cleanup the configuration artifacts
    const conditionName = configurationPage.getConfigurationName();
    deleteConfigurationArtifacts(conditionName);
  },
});
