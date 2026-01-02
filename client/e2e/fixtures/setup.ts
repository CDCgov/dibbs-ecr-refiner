import { test as baseTest, expect, Page, WorkerInfo } from '@playwright/test';
import { deleteConfigurationArtifacts, login } from '../utils';
import fs from 'fs';
import path from 'path';
class ConfigurationPage {
  private readonly conditionIndex: number;
  private conditionName: string = '';
  private conditionId: string = '';

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

const defaultFixturesTest = baseTest.extend<
  object,
  { workerStorageState: string }
>({
  storageState: ({ workerStorageState }, use) => use(workerStorageState),

  workerStorageState: [
    async ({ browser }, use) => {
      // Use parallelIndex as a unique identifier for each worker.
      const id = test.info().parallelIndex;
      // playwright will cache and use session authentication cookies here for reuse
      const fileName = path.resolve(
        test.info().project.outputDir,
        `.auth/${id}.json`
      );

      if (fs.existsSync(fileName)) {
        // Reuse existing authentication state if any.
        await use(fileName);
        return;
      }

      // Important: make sure we authenticate in a clean environment by unsetting storage state.
      const page = await browser.newPage({ storageState: undefined });
      // pass in the base URL directly since the value defined in playwright configs isn't accessible yet in the default fixtures
      await login(page, 'http://localhost:8081');

      await page.context().storageState({ path: fileName });
      await page.close();
      await use(fileName);
    },
    { scope: 'worker' },
  ],
  page: async ({ page }, use) => {
    // start in the logged in homepage
    await page.goto('/configurations');
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
