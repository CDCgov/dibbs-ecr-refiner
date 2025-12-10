import { Page, expect as baseExpect } from '@playwright/test';
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

export async function login(page: Page) {
  await page.goto('/');
  await page.getByText('Log in').click();
  await page.getByRole('textbox', { name: 'Username or email' }).click();
  await page
    .getByRole('textbox', { name: 'Username or email' })
    .fill('refiner');
  await page.getByRole('textbox', { name: 'Username or email' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('refiner');
  await page.getByRole('button', { name: 'Sign In' }).click();
  // check that we are on the logged-in home screen
  await baseExpect(
    page.getByText('Your reportable condition configurations')
  ).toBeVisible();
}

export async function logout(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'refiner' }).click();
  await page.getByRole('menuitem', { name: 'Log out' }).click();
  await baseExpect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
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
  await page.getByTestId('modalFooter').getByTestId('button').click();
  await baseExpect(
    page.getByRole('heading', { name: 'New configuration created' })
  ).toBeVisible();
}
