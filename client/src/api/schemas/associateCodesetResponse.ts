
/**
 * Response from adding a code set to a config.
 */
export interface AssociateCodesetResponse {
  id: string;
  included_conditions: string[];
  condition_name: string;
}
