import type { CodeCategoryStatus } from './codeCategoryStatus';

/**
 * Code category completeness status model.
 */
export interface CodeCategoryCompletenessStatus {
  category: string;
  name: string;
  completeness: CodeCategoryStatus;
}
