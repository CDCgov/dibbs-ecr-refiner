import type { CodeSystemFilterOption } from './codeSystemFilterOption';
import type { SourceFilterOption } from './sourceFilterOption';
import type { StatusFilterOption } from './statusFilterOption';

/**
 * Every filter option available for a configuration's codes.
 */
export interface CodeFilterOptionsResponse {
  code_systems: CodeSystemFilterOption[];
  sources: SourceFilterOption[];
  statuses: StatusFilterOption[];
}
