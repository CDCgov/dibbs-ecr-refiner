import { Pool } from 'pg';

/**
 * db is not a fixture so that it's not spun up and torn down on a per-test basis.
 *
 * NOTE: Don't import `db` directly! Please add a function to this file so queries are centralized.
 */
export const db = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'refiner',
  password: 'refiner',
  port: 5432,
});

export async function deleteAllCustomCodes(): Promise<void> {
  await db.query('DELETE FROM custom_codes');
}

export async function deleteAllConfigurations(): Promise<void> {
  await db.query('DELETE FROM configurations');
}

export async function clearDb(): Promise<void> {
  await deleteAllCustomCodes();
  await deleteAllConfigurations();
  await clearUserNotifications();
}

export async function clearUserNotifications(): Promise<void> {
  await db.query(
    "UPDATE users SET notifications = '{}'::jsonb WHERE username = 'refiner'"
  );
}
