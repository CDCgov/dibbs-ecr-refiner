import { Page, expect } from '@playwright/test';

export async function login(page: Page) {
  await page.goto('http://localhost:8081/');
  await page.getByText('Log in').click();
  await page.getByRole('textbox', { name: 'Username or email' }).click();
  await page
    .getByRole('textbox', { name: 'Username or email' })
    .fill('refiner');
  await page.getByRole('textbox', { name: 'Username or email' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('refiner');
  await page.getByRole('button', { name: 'Sign In' }).click();
}

export async function logout(page: Page) {
  await page.goto('http://localhost:8081/');
  await page.getByRole('button', { name: 'refiner' }).click();
  await page.getByRole('menuitem', { name: 'Logout' }).click();
  await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
}
