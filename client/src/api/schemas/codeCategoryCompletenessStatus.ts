import type { CodeCategoryCompletenessStatusCompleteness } from './codeCategoryCompletenessStatusCompleteness';

/**
 * Code category completeness status model.
 */
export interface CodeCategoryCompletenessStatus {
  category: string;
  name: string;
  completeness: CodeCategoryCompletenessStatusCompleteness;
}
