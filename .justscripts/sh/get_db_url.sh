#!/usr/bin/env sh
set -e

# Ensure an environment argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <environment>"
  echo "Available environments: local, demo, prod"
  exit 1
fi

ENV=$1

# Define database URLs for each environment
case "$ENV" in
  local)
    DB_URL="postgresql://postgres:refiner@db:5432/refiner?sslmode=disable"
    ;;
  demo)
    DB_URL=$(just cloud demo-db-url)
    ;;
  prod)
    DB_URL="postgresql://postgres:refiner@prod-db-host:5432/refiner?sslmode=require"
    ;;
  *)
    echo "Unknown environment: $ENV"
    echo "Available environments: local, demo, prod"
    exit 1
    ;;
esac

# Print the database URL
echo "$DB_URL"
