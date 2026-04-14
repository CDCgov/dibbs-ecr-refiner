import { Page, expect } from '@playwright/test';
import { execSync } from 'child_process';

export function refreshDatabase(): string {
  try {
    const output = execSync('just db refresh', { encoding: 'utf-8' });
    return output;
  } catch (error: unknown) {
    if (typeof error === 'object' && error !== null) {
      const err = error as { stderr?: string; message?: string };
      if (err.stderr) {
        throw new Error(String(err.stderr));
      } else if (err.message) {
        throw new Error(String(err.message));
      } else {
        throw new Error(JSON.stringify(err));
      }
    }
    throw new Error(String(error));
  }
}

export function deleteConfigurationArtifacts(conditionName: string): string {
  try {
    execSync(`just db delete-configuration '${conditionName}'`, {
      encoding: 'utf-8',
    });
    return 'Successfully cleaned up e2e configuration artifacts';
  } catch (error: unknown) {
    if (typeof error === 'object' && error !== null) {
      const err = error as { stderr?: string; message?: string };
      if (err.stderr) {
        throw new Error(String(err.stderr));
      } else if (err.message) {
        throw new Error(String(err.message));
      } else {
        throw new Error(JSON.stringify(err));
      }
    }
    throw new Error(String(error));
  }
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

export async function logout(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'refiner' }).click();
  await page.getByRole('menuitem', { name: 'Log out' }).click();
  await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
}

export async function createNewConfiguration(
  conditionName: string,
  page: Page
) {
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
