import type { StatusFilterOptionLabel } from './statusFilterOptionLabel';
import type { StatusFilterOptionStatus } from './statusFilterOptionStatus';

/**
 * Model to represent a status filter option.
 */
export interface StatusFilterOption {
  label: StatusFilterOptionLabel;
  status: StatusFilterOptionStatus;
  code_count: number;
}
