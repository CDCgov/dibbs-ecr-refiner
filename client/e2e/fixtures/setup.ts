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
    await expect(
      page.getByRole('heading', { name: 'Set up new configuration', level: 2 })
    ).toBeVisible();
    await page.getByLabel('Select condition').click();

    await page.getByRole('option').nth(this.conditionIndex).click();

    await page.keyboard.press('Enter');
    const createdConfigurationName = await page
      .getByLabel('Select condition')
      .inputValue();

    this.conditionName = createdConfigurationName;

    await page.getByRole('button', { name: 'Set up configuration' }).click();

    await expect(
      page.getByRole('heading', { name: this.conditionName, level: 1 })
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
      await login({ page, baseUrl: 'http://localhost:8081' });
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
