#!/usr/bin/env bash
set -euo pipefail # exit on failure

# Ensure both expected variables are present
if [[ -z "${DB_URL:-}" || -z "${DB_PASSWORD:-}" ]]; then
  echo "ERROR: DB_URL and DB_PASSWORD must be set"
  exit 1
fi

# Encode DB_PASSWORD
ENCODED_PASSWORD=$(python3 -c 'import urllib.parse, os; print(urllib.parse.quote(os.environ["DB_PASSWORD"]))')

# Compose DATABASE_URL for migrations
if [[ "$DB_URL" == *\?* ]]; then
    # Already has query params, append password and sslmode
    DATABASE_URL="${DB_URL}&password=${ENCODED_PASSWORD}&sslmode=disable"
else
    DATABASE_URL="${DB_URL}?password=${ENCODED_PASSWORD}&sslmode=disable"
fi

# Backup if no command is given
if [ $# -eq 0 ]; then
    echo "No command supplied, dropping into bash"
    exec bash
fi

# -----------------------------
# Run migrate or python scripts
# -----------------------------
COMMAND="$1"
shift || true

case "$COMMAND" in
    migrate)
        echo "Running migrations with args: $*"
        exec migrate -path ./migrations -database "$DATABASE_URL" "$@"
        ;;
    import)
        echo "Importing condition data"
        exec python3 ./scripts/seeding/seed_db.py
        ;;
    python|python3)
        echo "Running Python script: $*"
        exec python3 "$@"
        ;;
    prepare-db)
        echo "Running migration scripts and updating condition data"
        migrate -path ./migrations -database "$DATABASE_URL" up
        exec python3 ./scripts/seeding/seed_db.py
        ;;
    *)
        echo "Running custom command: $COMMAND $*"
        exec "$COMMAND" "$@"
        ;;
esac
