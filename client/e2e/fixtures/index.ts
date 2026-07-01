import {
  mergeTests,
  mergeExpects,
  expect as baseExpect,
  test as baseTest,
} from '@playwright/test';
import { ConfigurationPage } from '../pages/ConfigurationPage';
import { ConfigurationsPage } from '../pages/ConfigurationsPage';
import { AxeBuilder } from '@axe-core/playwright';
import { SimulatorPage } from '../pages/SimulatorPage';
import { Api } from './api';
import { ActivityLogPage } from '../pages/ActivityLogPage';

interface Fixtures {
  configurationPage: ConfigurationPage;
  configurationsPage: ConfigurationsPage;
  simulatorPage: SimulatorPage;
  activityLogPage: ActivityLogPage;
  makeAxeBuilder: () => AxeBuilder;
  api: Api;
}

const extendedTest = baseTest.extend<Fixtures>({
  makeAxeBuilder: async ({ page }, use) => {
    const makeAxeBuilder = () =>
      new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .exclude('#refinement-diff'); // react-diff-viewer has known a11y issues we can't fix ourselves
    await use(makeAxeBuilder);
  },
  api: async ({ request }, use) => {
    await use(new Api(request));
  },
  configurationPage: async ({ page }, use) => {
    await use(new ConfigurationPage(page));
  },
  configurationsPage: async ({ page }, use) => {
    await use(new ConfigurationsPage(page));
  },
  simulatorPage: async ({ page }, use) => {
    await use(new SimulatorPage(page));
  },
  activityLogPage: async ({ page }, use) => {
    await use(new ActivityLogPage(page));
  },
});

const extendedExpect = baseExpect.extend({
  async toHaveNoAxeViolations(makeAxeBuilder: () => AxeBuilder) {
    const assertionName = 'toHaveNoAxeViolations';
    const axe = makeAxeBuilder();
    let pass = false;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let violations: any[] = [];
    try {
      const results = await axe.analyze();
      violations = results.violations ?? [];
      pass = violations.length === 0;
    } catch {
      pass = false;
    }

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

export const expect = mergeExpects(extendedExpect);
export const test = mergeTests(extendedTest);
