#!/bin/sh

# this script will be executed by the postgres entrypoint script
# after the database has been created and is ready to accept connections

set -e

echo "🌱 [CUSTOM SCRIPT] Running Python database seeder..."

# set the standard PGUSER and PGDATABASE environment variables
# * the entrypoint script provides POSTGRES_USER and POSTGRES_DB
# * our python script will automatically use these to connect
export PGUSER="${POSTGRES_USER}"
export PGDATABASE="${POSTGRES_DB}" # This is the new line

# now run the python script
python3 /app/scripts/database_seeding.py

echo "✅ [CUSTOM SCRIPT] Seeding complete."
