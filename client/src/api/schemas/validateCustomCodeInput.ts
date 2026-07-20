
/**
 * Input model when validating a config's custom code.
 */
export interface ValidateCustomCodeInput {
  current_code: string | null;
  desired_code: string;
}
