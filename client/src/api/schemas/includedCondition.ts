
/**
 * Model for a condition that is associated with a configuration.
 */
export interface IncludedCondition {
  id: string;
  display_name: string;
  canonical_url: string;
  version: string;
  associated: boolean;
}
