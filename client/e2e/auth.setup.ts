import { test as setup } from '@playwright/test';
import fs from 'fs';
import { login } from './utils';

const authFile = 'e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  if (fs.existsSync(authFile)) fs.unlinkSync(authFile);
  await login({ page });
  await page.context().storageState({ path: authFile });
});
