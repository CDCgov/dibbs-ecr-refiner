import type { CodeCategoryStatus } from './codeCategoryStatus';

/**
 * Code category completeness status model.
 */
export interface CodeCategoryCompletenessStatus {
  category: string;
  display_name: string;
  completeness: CodeCategoryStatus;
}
