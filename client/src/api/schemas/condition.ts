
/**
 * Model for a Condition.
 */
export interface Condition {
  code: string;
  display_name: string;
  refined_eicr: string;
  stats: string[];
  render_diff: boolean;
}
