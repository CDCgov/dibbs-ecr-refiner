import { Pool } from 'pg';

export const db = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'refiner',
  password: 'refiner',
  port: 5432,
});

export async function deleteConfigurationArtifacts(
  conditionName: string
): Promise<void> {
  await db.query(
    'DELETE FROM configurations_locks WHERE configuration_id IN (SELECT id FROM configurations WHERE name = $1)',
    [conditionName]
  );
  await db.query(
    'DELETE FROM events WHERE configuration_id IN (SELECT id FROM configurations WHERE name = $1)',
    [conditionName]
  );
  await db.query('DELETE FROM configurations WHERE name = $1', [conditionName]);
}
