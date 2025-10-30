import { expect as baseExpect } from '@playwright/test';
import type { AxeBuilder } from '@axe-core/playwright';

export { test } from '@playwright/test';

export const expect = baseExpect.extend({
  async toHaveNoAxeViolations(makeAxeBuilder: () => AxeBuilder) {
    const assertionName = 'toHaveNoAxeViolations';
    const axe = makeAxeBuilder();
    const results = await axe.analyze();
    const violations = results.violations ?? [];

    const pass = violations.length === 0;

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
