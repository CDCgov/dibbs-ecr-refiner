import type { NotificationInfo } from './notificationInfo';

/**
 * List of notification information to return to frontend.
 */
export interface NotificationResponse {
  most_recent_app_update: NotificationInfo;
}
