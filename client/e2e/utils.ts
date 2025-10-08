import { Page, expect } from '@playwright/test';
import { execSync } from 'child_process';
import AxeBuilder, { AxeResults, RunOptions } from '@axe-core/playwright';

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
}

export async function logout(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'refiner' }).click();
  await page.getByRole('menuitem', { name: 'Log out' }).click();
  await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
}

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

/**
 * Runs Axe accessibility checks using best-practice configuration (WCAG 2.1 AA) and fails the test on violations.
 * Prints all detected accessibility violations to the Playwright console output for debugging.
 *
 * @param {Page} page - The Playwright Page object to run accessibility checks against.
 * @param {Partial<RunOptions>} [options] - Optional Axe run options (e.g., exclude selectors).
 * @throws Will fail the test if any accessibility violations are found.
 */
export async function runAxeAccessibilityCheck(page: Page, options: Partial<RunOptions> = {}) {
  const results: AxeResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    // .configure({ rules: { 'color-contrast': { enabled: true } } }) // enforce color contrast check
    .options(options)
    .analyze();

  if (results.violations.length > 0) {
    // Print violations in a readable format for debugging
    console.error('[A11Y] Accessibility Violations:',
      results.violations.map((v: typeof results.violations[number]) => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        nodes: v.nodes.map((n: typeof v.nodes[number]) => n.target)
      }))
    );
  }
  expect(results.violations, 'No accessibility violations').toEqual([]);
}
