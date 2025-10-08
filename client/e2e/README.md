# End-to-End Testing with Playwright

This project uses [Playwright](https://playwright.dev/) for end-to-end (E2E) browser testing with TypeScript. All E2E tests live in the `client/e2e/` directory.

## How to Run E2E Tests Locally

1. **Make sure dependencies and browsers are installed:**
   - `npm install`
   - `npx playwright install`

2. **Start your development server:**
   - Make sure your app (e.g., Vite) is running on `http://localhost:8081` (or update `playwright.config.ts` to point to the correct dev URL).

3. **Run the E2E tests:**
   - `npm run e2e`
   - By default, tests run in headless mode across Chromium, Firefox, and WebKit.

4. **View the HTML test report:**
   - After running, show the report with `npm run e2e:report`

## Writing E2E Tests

- Add new tests as `.spec.ts` files in `client/e2e/`.
- Use Playwright's [test](https://playwright.dev/docs/writing-tests) API and [locators](https://playwright.dev/docs/locators) for resilient, readable tests.
- Example test:

```ts
import { test, expect } from '@playwright/test';

test('homepage loads', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/CDC/);
});
```

- Use `test.beforeEach()` for setup (like navigation or login) if needed.
- Prefer user-facing locators (roles, labels, text) over CSS selectors.

## Accessibility (a11y) Testing

- All E2E flows are required to include automated accessibility checks using [Axe](https://www.deque.com/axe/) via the [`@axe-core/playwright`](https://github.com/dequelabs/axe-core-playwright) integration.
- Use the shared `runAxeAccessibilityCheck(page)` utility (from `utils.ts`) after any major navigation or UI state change in your tests.
- Accessibility violations will cause the test to fail and print a summary to the Playwright output.
- Axe is configured for WCAG 2.1 AA and common false positives are minimized by default.
- Example usage:

```ts
import { runAxeAccessibilityCheck } from './utils';

test('my accessible page', async ({ page }) => {
  await page.goto('/my-page');
  await runAxeAccessibilityCheck(page); // checks current DOM for a11y issues
});
```

- See [`utils.ts`](./utils.ts) for JSDoc and configuration details.

## Best Practices

- Tests should be isolated and not depend on data from other tests.
- Use [web-first assertions](https://playwright.dev/docs/test-assertions) (`await expect(...)`), not manual assertions.
- Avoid testing third-party sites or dependencies you don't control.
- Run tests across all major browsers (Chromium, Firefox, WebKit) for full coverage.
- Keep Playwright and browser binaries up-to-date: `npm install -D @playwright/test@latest` and `npx playwright install --with-deps`
- Use ESLint and TypeScript for linting and type safety.

## Continuous Integration (CI)

- E2E tests are run on every pull request and push (see `.github/workflows/playwright.yml`).
- The HTML report will be uploaded as a workflow artifact for easy download and inspection.

## Debugging

- Run with `npx playwright test --headed` to see the browser UI.
- Use `npx playwright test --ui` for interactive mode and time-travel debugging.
- Use `npx playwright test --debug` for detailed step-by-step debugging.

## Useful Resources

- [Playwright Docs](https://playwright.dev/docs/intro)
- [Writing Tests](https://playwright.dev/docs/writing-tests)
- [Locators](https://playwright.dev/docs/locators)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [CI Integration](https://playwright.dev/docs/ci-intro)
