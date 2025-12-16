import { mergeTests, mergeExpects } from '@playwright/test';
import { expect as axeExpect, test as axeTest } from './axe';
import { test as loggedInTest } from './setup';

export const expect = mergeExpects(axeExpect);
export const test = mergeTests(axeTest, loggedInTest);
