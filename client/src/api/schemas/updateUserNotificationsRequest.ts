
/**
 * Request to update notification acknowledgement state for the current user.
 */
export interface UpdateUserNotificationsRequest {
  name: string;
  date_acknowledged: string;
}
