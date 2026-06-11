
/**
 * Input model when updating a config's custom code.
 */
export interface UpdateCustomCodeInput {
  system_key: string;
  code: string;
  name: string;
  new_code: string | null;
  new_system_key: string | null;
  new_name: string | null;
}
