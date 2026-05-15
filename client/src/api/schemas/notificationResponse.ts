import type { NotificationInfo } from './notificationInfo';

/**
 * Notification information needed to render frontend banners.
 */
export interface NotificationResponse {
  most_recent_app_update: NotificationInfo;
}
