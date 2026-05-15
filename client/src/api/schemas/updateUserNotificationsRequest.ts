import type { NotificationKeys } from './notificationKeys';

/**
 * Request to update notification acknowledgement state for the current user.
 */
export interface UpdateUserNotificationsRequest {
  key: NotificationKeys;
}
