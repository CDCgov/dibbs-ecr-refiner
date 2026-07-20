import type { AuditEvent } from './auditEvent';
import type { EventFilterOption } from './eventFilterOption';

/**
 * Response needed for the audit log page.
 */
export interface EventsResponse {
  audit_events: AuditEvent[];
  configuration_options: EventFilterOption[];
  total_pages: number;
}
