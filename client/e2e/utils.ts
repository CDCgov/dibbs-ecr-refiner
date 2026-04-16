import { Page, expect } from '@playwright/test';
import path from 'path';

export async function uploadMonmothmaTestFile(page: Page) {
  const filePath = path.resolve(
    process.cwd(),
    'e2e/assets/mon-mothma-two-conditions.zip'
  );
  await page.locator('input#zip-upload').setInputFiles(filePath);
  await page.getByText('Refine .zip file').click();
}

export async function login({
  page,
  user,
  baseUrl = '/',
}: {
  page: Page;
  user?: string | null;
  baseUrl?: string;
}) {
  const username = typeof user === 'string' ? user : 'refiner';
  const password = typeof user === 'string' ? user : 'refiner';

  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });

  await page.getByText('Log in').click();
  await page.getByRole('textbox', { name: 'Username or email' }).fill(username);
  await page.getByRole('textbox', { name: 'Password' }).fill(password);

  // wait for navigation after clicking sign in button
  await Promise.all([
    page.waitForURL('http://localhost:8081/configurations', {
      timeout: 30000,
    }),
    page.getByRole('button', { name: 'Sign In' }).click(),
  ]);

  // check that we are on the logged-in home screen
  await expect(
    page.getByRole('heading', { name: 'Configurations' })
  ).toBeVisible();
}
