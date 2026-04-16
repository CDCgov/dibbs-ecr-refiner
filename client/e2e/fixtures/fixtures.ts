import {
  mergeTests,
  mergeExpects,
  expect as baseExpect,
  test as baseTest,
} from '@playwright/test';
import { ConfigurationPage } from '../pages/ConfigurationPage';
import { ConfigurationsPage } from '../pages/ConfigurationsPage';
import { AxeBuilder } from '@axe-core/playwright';
import { TestingPage } from '../pages/TestingPage';
import { Api } from './api';

type Fixtures = {
  configurationPage: ConfigurationPage;
  configurationsPage: ConfigurationsPage;
  testingPage: TestingPage;
  makeAxeBuilder: () => AxeBuilder;
  api: Api;
};

const extendedTest = baseTest.extend<Fixtures>({
  makeAxeBuilder: async ({ page }, use) => {
    const makeAxeBuilder = () =>
      new AxeBuilder({ page }).withTags(['wcag21aa']);
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
  testingPage: async ({ page }, use) => {
    await use(new TestingPage(page));
  },
});

const extendedExpect = baseExpect.extend({
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

export const expect = mergeExpects(extendedExpect);
export const test = mergeTests(extendedTest);
