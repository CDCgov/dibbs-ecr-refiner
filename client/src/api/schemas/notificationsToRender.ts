import type { NotificationKeys } from './notificationKeys';

/**
 * Map of booleans for each of the notificaiton keys as to whether to render frontend banners.
 */
export interface NotificationsToRender {
  to_render: Partial<Record<NotificationKeys, boolean>>;
}
