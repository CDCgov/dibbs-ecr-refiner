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
  await page.goto('/configurations');
  await page.getByRole('button', { name: 'Set up new configuration' }).click();
  await expect(
    page.getByRole('heading', { name: 'Set up new configuration', level: 2 })
  ).toBeVisible();
  await page.getByLabel('Select condition').fill(conditionName);
  await page.getByLabel('Select condition').press('Enter');
  await expect(
    page.getByRole('button', { name: 'Set up configuration' })
  ).toBeEnabled();
  await page.getByRole('button', { name: 'Set up configuration' }).click();
  await expect(
    page.getByRole('heading', { name: conditionName, level: 1 })
  ).toBeVisible();
}

export async function createAndActivateCovidConfig(page: Page) {
  await createNewConfiguration('COVID-19', page);
  await page.getByRole('link', { name: 'Activate' }).click();
  await page.getByRole('button', { name: 'Turn on configuration' }).click();
  await page
    .getByRole('button', { name: 'Yes, turn on configuration' })
    .click();
}

export async function createAndActivateInfluenzaConfig(page: Page) {
  await createNewConfiguration('Influenza', page);
  await page.getByRole('link', { name: 'Activate' }).click();
  await page.getByRole('button', { name: 'Turn on configuration' }).click();
  await page
    .getByRole('button', { name: 'Yes, turn on configuration' })
    .click();
}
