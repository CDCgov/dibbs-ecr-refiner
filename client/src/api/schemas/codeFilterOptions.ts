import type { CodeSystemFilterOption } from './codeSystemFilterOption';
import type { SourceFilterOption } from './sourceFilterOption';
import type { StatusFilterOption } from './statusFilterOption';

/**
 * Model to represent all filter options available to the client.
 */
export interface CodeFilterOptions {
  code_systems: CodeSystemFilterOption[];
  sources: SourceFilterOption[];
  statuses: StatusFilterOption[];
}
