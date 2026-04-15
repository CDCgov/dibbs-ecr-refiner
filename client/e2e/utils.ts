import { Page, expect } from '@playwright/test';

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

export async function createNewConfiguration(
  conditionName: string,
  page: Page
) {
  await page.getByRole('button', { name: 'Set up new configuration' }).click();
  await page.getByTestId('combo-box-input').click();
  await page.getByTestId('combo-box-input').fill(conditionName);
  await page.getByTestId('combo-box-input').press('Tab');
  await page
    .getByRole('option', { name: conditionName, exact: true })
    .press('Enter');
  await page.getByTestId('combo-box-input').press('Tab');
  await page.getByTestId('combo-box-clear-button').press('Tab');
  await expect(
    page.getByRole('button', { name: 'Set up configuration' })
  ).toBeEnabled();
  await page.getByRole('button', { name: 'Set up configuration' }).click();
  await expect(
    page.locator(
      `h4:has-text("New configuration created") + p:has-text("${conditionName}")`
    )
  ).toBeVisible();
}
