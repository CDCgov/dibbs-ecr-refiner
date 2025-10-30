import { test as base } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// See here: https://playwright.dev/docs/accessibility-testing#creating-a-fixture

export type AxeFixture = {
  makeAxeBuilder: () => AxeBuilder;
};

export const test = base.extend<AxeFixture>({
  makeAxeBuilder: async ({ page }, use) => {
    const makeAxeBuilder = () =>
      new AxeBuilder({ page }).withTags(['wcag21aa']);

    // eslint-disable-next-line react-hooks/rules-of-hooks
    await use(makeAxeBuilder);
  },
});

export { expect } from '@playwright/test';
