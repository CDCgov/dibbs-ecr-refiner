import { expect as baseExpect, test as baseTest } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

// See here: https://playwright.dev/docs/accessibility-testing#creating-a-fixture

export type AxeFixture = {
  makeAxeBuilder: () => AxeBuilder;
};

const test = baseTest.extend<AxeFixture>({
  makeAxeBuilder: async ({ page }, use) => {
    const makeAxeBuilder = () =>
      new AxeBuilder({ page }).withTags(['wcag21aa']);

    await use(makeAxeBuilder);
  },
});

const expect = baseExpect.extend({
  async toHaveNoAxeViolations(makeAxeBuilder: () => AxeBuilder) {
    const assertionName = 'toHaveNoAxeViolations';
    const axe = makeAxeBuilder();
    let pass: boolean;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let results: any;
    try {
      results = await axe.analyze();
    } catch {
      pass = false;
    }
    const violations = results.violations ?? [];

    pass = violations.length === 0;

    const message = pass
      ? () =>
          this.utils.matcherHint(assertionName, undefined, undefined, {
            isNot: this.isNot,
          }) +
          '\n\n' +
          'No accessibility violations found'
      : () =>
          this.utils.matcherHint(assertionName, undefined, undefined, {
            isNot: this.isNot,
          }) +
          '\n\n' +
          `Found ${violations.length} accessibility violation(s):\n` +
          JSON.stringify(violations, null, 2);

    return {
      message,
      pass,
      name: assertionName,
      expected: 'no axe violations',
      actual: `${violations.length} violation(s)`,
    };
  },
});

export { test, expect };
