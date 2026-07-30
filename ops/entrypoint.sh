#!/usr/bin/env bash
set -euo pipefail # exit on failure

# default sslmode to "require"
SSL_MODE="${SSL_MODE:-require}"

# Ensure required variables are present
if [[ -z "${ENV:-}" || \
      -z "${VERSION:-}" || \
      -z "${DB_URL:-}" || \
      -z "${DB_PASSWORD:-}" || \
      -z "${AWS_REGION:-}" || \
      -z "${S3_BUCKET_CONFIG:-}" ]]; then
  echo "ERROR: ENV, VERSION, DB_URL, DB_PASSWORD, AWS_REGION, and S3_BUCKET_CONFIG must be set"
  exit 1
fi

# Ensure local/demo S3 variables are present
if [[ "${ENV}" == "local" || "${ENV}" == "demo" ]]; then
  if [[ -z "${AWS_ACCESS_KEY_ID:-}" || \
        -z "${AWS_SECRET_ACCESS_KEY:-}" || \
        -z "${S3_ENDPOINT_URL:-}" ]]; then
    echo "ERROR: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_ENDPOINT_URL must be set for local/demo"
    exit 1
  fi
fi

# Encode DB_PASSWORD
ENCODED_PASSWORD=$(python3 -c 'import urllib.parse, os; print(urllib.parse.quote(os.environ["DB_PASSWORD"]))')

# Compose DATABASE_URL for migrations
if [[ "$DB_URL" == *\?* ]]; then
    # Already has query params, append password and sslmode
    DATABASE_URL="${DB_URL}&password=${ENCODED_PASSWORD}&sslmode=${SSL_MODE}"
else
    DATABASE_URL="${DB_URL}?password=${ENCODED_PASSWORD}&sslmode=${SSL_MODE}"
fi

# Backup if no command is given
if [ $# -eq 0 ]; then
    echo "No command supplied, dropping into bash"
    exec bash
fi

# Run migrate or python scripts
COMMAND="$1"
shift || true

case "$COMMAND" in
    migrate)
        echo "Running migrations with args: $*"
        exec dbmate --no-dump-schema --migrations-dir ./migrations --url "$DATABASE_URL" "$@"
        ;;
    import)
        echo "Importing static data"
        exec python3 ./scripts/seeding/load_static_data.py
        ;;
    regenerate-active-configs)
        echo "Regenerating active configuration files"
        exec python3 ./scripts/reactivations/regenerate_active_configs.py "$@"
        ;;
    python|python3)
        echo "Running Python script: $*"
        exec python3 "$@"
        ;;
    prepare-db)
        echo "Running migration scripts and updating condition data"
        dbmate --no-dump-schema --migrations-dir ./migrations --url "$DATABASE_URL" migrate
        echo "Migration step complete"
        python3 ./scripts/seeding/load_static_data.py
        echo "Regenerating active configuration files"
        python3 ./scripts/reactivations/regenerate_active_configs.py
        ;;
    *)
        echo "Running custom command: $COMMAND $*"
        exec "$COMMAND" "$@"
        ;;
esac
