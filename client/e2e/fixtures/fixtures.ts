import { mergeTests, mergeExpects } from '@playwright/test';
import { expect as axeExpect, test as axeTest } from './axe';

export const expect = mergeExpects(axeExpect);
export const test = mergeTests(axeTest);
