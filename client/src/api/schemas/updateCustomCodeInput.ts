
/**
 * Input model when updating a config's custom code.
 */
export interface UpdateCustomCodeInput {
  system_id: string;
  code: string;
  name: string;
  new_code: string | null;
  new_system_id: string | null;
  new_name: string | null;
}
