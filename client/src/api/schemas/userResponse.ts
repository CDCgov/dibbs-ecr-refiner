import type { UserNotifications } from './userNotifications';

/**
 * User information to send to the client.
 */
export interface UserResponse {
  id: string;
  username: string;
  jurisdiction_id: string;
  notifications: UserNotifications;
}
