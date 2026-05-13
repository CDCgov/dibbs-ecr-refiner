
/**
 * An event returned by the DB function.
 */
export interface AuditEvent {
  id: string;
  username: string;
  configuration_name: string;
  configuration_version: number;
  condition_id: string;
  action_text: string;
  created_at: string;
  has_custom_code_upload_events: boolean;
}
