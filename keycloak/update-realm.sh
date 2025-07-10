#!/bin/bash

# REQUIREMENTS:
# - curl
# - jq

# CONFIGURATION
KEYCLOAK_HOST="http://localhost:8082"
REALM_NAME="refiner"
ADMIN_USER="admin"
ADMIN_PASS="admin"
CLIENT_ID="admin-cli"

echo "🔐 Getting access token..."
ACCESS_TOKEN=$(curl -s -X POST "${KEYCLOAK_HOST}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}" \
  -d "password=${ADMIN_PASS}" \
  -d "grant_type=password" \
  -d "client_id=${CLIENT_ID}" | jq -r .access_token)

if [[ -z "$ACCESS_TOKEN" || "$ACCESS_TOKEN" == "null" ]]; then
  echo "❌ Failed to get access token. Check credentials and server status."
  exit 1
fi

echo "✅ Token acquired."

# Base URL for Admin API
API="${KEYCLOAK_HOST}/admin/realms/${REALM_NAME}"

# Temporary files
TMP_DIR=$(mktemp -d)
REALM_FILE="${TMP_DIR}/realm.json"
CLIENTS_FILE="${TMP_DIR}/clients.json"
ROLES_FILE="${TMP_DIR}/roles.json"
USERS_FILE="${TMP_DIR}/users.json"

echo "📥 Fetching realm core config..."
curl -s -X GET "${API}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -o "$REALM_FILE"

echo "📥 Fetching clients..."
curl -s -X GET "${API}/clients?viewableOnly=true" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -o "$CLIENTS_FILE"

echo "📥 Fetching roles..."
curl -s -X GET "${API}/roles" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -o "$ROLES_FILE"

echo "📥 Fetching users..."
curl -s -X GET "${API}/users" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -o "$USERS_FILE"

echo "🧩 Assembling full realm file..."

# Combine everything into a single JSON structure
jq -n \
  --argjson realm "$(cat "$REALM_FILE")" \
  --argjson clients "$(cat "$CLIENTS_FILE")" \
  --argjson roles "$(cat "$ROLES_FILE")" \
  --argjson users "$(cat "$USERS_FILE")" \
  '
  $realm +
  {
    clients: $clients,
    roles: {
      realm: $roles
    },
    users: $users
  }
  ' > "./${REALM_NAME}-realm.json"

echo "✅ Full realm exported to: ${REALM_NAME}-realm.json"

# Clean up
rm -rf "$TMP_DIR"
