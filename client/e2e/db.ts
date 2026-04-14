import { Pool } from 'pg';
export const db = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'refiner',
  password: 'refiner',
  port: 5432,
});
