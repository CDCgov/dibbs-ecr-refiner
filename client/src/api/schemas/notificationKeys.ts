
/**
 * Enum class to type the values of the notifications possible for actioning on the frontend.
 */
export type NotificationKeys = typeof NotificationKeys[keyof typeof NotificationKeys];


export const NotificationKeys = {
  most_recent_app_update: 'most_recent_app_update',
  most_recent_tes_update: 'most_recent_tes_update',
} as const;
