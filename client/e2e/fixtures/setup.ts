import { test as baseTest } from '@playwright/test';
import { login } from '../utils';
import fs from 'fs';
import path from 'path';

export const test = baseTest.extend<object, { workerStorageState: string }>({
  // eslint-disable-next-line react-hooks/rules-of-hooks
  storageState: ({ workerStorageState }, use) => use(workerStorageState),

  workerStorageState: [
    async ({ browser }, use) => {
      // Use parallelIndex as a unique identifier for each worker.
      const id = test.info().parallelIndex;
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
      // pass in the base URL directly since it doesn't seem to be picking up the value from the config for some reason
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
    // eslint-disable-next-line react-hooks/rules-of-hooks
    await use(page);
  },
});
