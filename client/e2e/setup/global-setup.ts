import { expect as customExpect } from '../utils/custom-matchers';
import { expect as baseExpect, test as baseTest } from '@playwright/test';
import { test as axeTest } from '../axe-test';

function globalSetup() {
  Object.assign(baseTest, axeTest);
  Object.assign(baseExpect, customExpect);
}

export default globalSetup;
