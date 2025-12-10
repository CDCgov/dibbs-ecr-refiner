import { test as baseTest } from '@playwright/test';
import { login, logout } from '../utils';

export const test = baseTest.extend({
  page: async ({ page }, use) => {
    await page.goto('/');
    await login(page);

    // Use signed-in page in the test.
    await page.goto('/configurations');

    // eslint-disable-next-line react-hooks/rules-of-hooks
    await use(page);

    await logout(page);
  },
});
