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
  await deleteAllCodeExclusions();
  await deleteAllConfigurations();
  await clearUserNotifications();
}

export async function deleteAllCodeExclusions(): Promise<void> {
  await db.query('DELETE FROM configurations_conditions_code_exclusions');
}

export async function clearUserNotifications(): Promise<void> {
  await db.query(
    "UPDATE users SET notifications = '{}'::jsonb WHERE username = 'refiner'"
  );
}

export async function makeOldTesVersionConfiguration(
  conditionName: string,
  status: 'active' | 'draft'
): Promise<void> {
  await db.query(
    `WITH condition_to_insert AS (
        SELECT c.display_name AS condition_name, c.id AS condition_id
        FROM conditions c
        LEFT JOIN tes t ON c.tes_id = t.id
        WHERE c.display_name = '${conditionName}' AND t.version = '5.0.0'
    ),
    inserted_config AS (
        INSERT INTO configurations (version, jurisdiction_id, status, name, created_by)
        SELECT
            1,
            'SDDH',
            '${status}',
            condition_name,
            (SELECT id FROM users WHERE username = 'refiner')
        FROM condition_to_insert
        RETURNING id, name
    )
    INSERT INTO configurations_conditions (configuration_id, condition_id, is_primary)
    SELECT ic.id, cti.condition_id, false
    FROM inserted_config ic
    JOIN condition_to_insert cti ON ic.name = cti.condition_name;
  `
  );
}
