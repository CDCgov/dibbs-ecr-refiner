import type { UserNotification } from './userNotification';

/**
 * User notification state.
 */
export interface UserNotifications {
  most_recent_app_update?: UserNotification | null;
}
