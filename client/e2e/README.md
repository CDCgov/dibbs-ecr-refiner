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
   - `npm run e2e:dev` can be used to run the tests using the visual runner

4. **View the HTML test report:**
   - After running, show the report with `npm run e2e:report`

## Writing E2E Tests

- Add new tests as `*.spec.ts` files in `client/e2e/`.
- Use Playwright's [test](https://playwright.dev/docs/writing-tests) API and [locators](https://playwright.dev/docs/locators) for resilient, readable tests.

### Page Object Models (POMs)

We make use of [page object models](https://playwright.dev/docs/pom) (found in [/pages](./pages/)) to enable us to write tests more quickly, limit maintenance, and improve general readability of tests.

POMs are available in all test code via fixtures.

### Making API Requests

All tests have access to an `api` fixture that allows us to make requests to the Refiner API. This is useful because we can avoid going through an unreleated UI flow to set up test data for what we want to test.

Please see [fixtures/api](fixtures/api.ts).

### Direct Database Access

> [!IMPORTANT]
> We should prefer to use API requests instead of direct database queries when possible. When we make use of API requests we are still testing public application functionality which is more beneficial to us than running DB queries.

Similar to API requests, direct database access allows us to perform operations that are not available through the API but are useful for testing, such as deleting configuration data.

Please see [db/index.ts](db/index.ts)

## Accessibility Checks

In order to perform automated Axe accessibility checks, we are able to make use of the `toHaveNoAxeViolations()` custom matcher. This matcher should be used any time the view changes for the user. This ensures that we are able to capture potential a11y issues on the various different states of a page.

> [!IMPORTANT]
> When writing tests, we must make sure that we are using `test` and `expect` from the `fixtures` directory. If we use `test` and `expect` from `@playwright/test` directly, it will not know about the custom matchers.

Here is an example of adding a11y checks to a test:

```typescript
import { test, expect } from './fixtures/fixtures';

test('checking for a11y issues on a page', async ({
   page,
   makeAxeBuilder,
}) => {
   // go to page and perform an a11y check
   await expect(page).toHaveTitle(/DIBBs eCR Refiner/);
   await expect(makeAxeBuilder).toHaveNoAxeViolations();

   ... // perform an action to open a modal, show a new component, etc. (new page state)

   // run an updated check on new elements
   await expect(makeAxeBuilder).toHaveNoAxeViolations();
});
```

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
