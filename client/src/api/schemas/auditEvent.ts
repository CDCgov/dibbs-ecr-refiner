
/**
 * One row of the audit log page.
 */
export interface AuditEvent {
  id: string;
  username: string;
  configuration_display_name: string;
  configuration_version: number;
  condition_id: string | null;
  action_text: string;
  code_count: number | null;
  created_at: string;
  event_type: string;
  has_custom_code_upload_events: boolean;
}
