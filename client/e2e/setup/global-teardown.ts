import { db } from '../db';

export default async function globalTeardown() {
  await db.end();
}
