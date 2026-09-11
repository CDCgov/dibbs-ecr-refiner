import type { CodeCategoryCompletenessStatus } from './codeCategoryCompletenessStatus';
import type { CodeSetStatus } from './codeSetStatus';

/**
 * Condition completeness status model.
 */
export interface CompletenessStatus {
  code_set_status: CodeSetStatus;
  code_category_statuses: CodeCategoryCompletenessStatus[];
}
