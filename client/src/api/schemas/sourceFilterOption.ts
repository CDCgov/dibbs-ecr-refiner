
/**
 * A code source the client can filter by -- a condition, or `None` for custom codes.
 */
export interface SourceFilterOption {
  condition_id: string | null;
  display_name: string;
  code_count: number;
}
