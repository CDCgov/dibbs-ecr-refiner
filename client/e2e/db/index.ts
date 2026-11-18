import { Pool } from 'pg';
import { PREVIOUS_TES_VERSION } from '../constants';

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
        WHERE c.display_name = '${conditionName}' AND t.version = '${PREVIOUS_TES_VERSION}'
    ),
    inserted_config AS (
        INSERT INTO configurations (version, jurisdiction_id, status, display_name, created_by)
        SELECT
            1,
            'SDDH',
            '${status}',
            condition_name,
            (SELECT id FROM users WHERE username = 'refiner')
        FROM condition_to_insert
        RETURNING id, display_name
    )
    INSERT INTO configurations_conditions (configuration_id, condition_id, is_primary)
    SELECT ic.id, cti.condition_id, true
    FROM inserted_config ic
    JOIN condition_to_insert cti ON ic.display_name = cti.condition_name;
  `
  );
}

export async function getConditionIdByName(
  conditionName: string
): Promise<string> {
  const latestConditionId = await db.query(`
    SELECT conditions.id
    FROM conditions 
    JOIN tes t on t.id = conditions.tes_id 
    WHERE display_name='${conditionName}'
    ORDER BY t.version DESC
    LIMIT 1;`);

  if (!latestConditionId || latestConditionId.rows.length === 0) {
    throw Error(
      `Requested condition ID for condition ${conditionName} not found`
    );
  }

  return latestConditionId.rows[0]['id'];
}

export async function getRsgSnomedCodesFromCondition(
  conditionName: string
): Promise<string[]> {
  const rsgSnomedCodes = await db.query(`
    WITH latest_condition AS (
      SELECT conditions.id
      FROM conditions 
      JOIN tes t ON t.id = conditions.tes_id 
      WHERE display_name = '${conditionName}'
      ORDER BY t.version DESC
      LIMIT 1 
  )
  SELECT codes.code
  FROM codes 
  LEFT JOIN conditions_codes_temp cc ON cc.code_id = codes.id 
  LEFT JOIN conditions c ON c.id = cc.condition_id 
  JOIN latest_condition lc ON c.id = lc.id
  WHERE cc.is_child_rsg;
  `);

  if (!rsgSnomedCodes || rsgSnomedCodes.rows.length === 0) {
    throw Error(
      `Requested condition ID for condition ${conditionName} not found`
    );
  }

  return rsgSnomedCodes.rows.map((c) => c['code']);
}
