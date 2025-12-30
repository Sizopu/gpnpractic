#!/bin/sh
set -e

STATUS_DIR="/usr/share/java/keycloak/status"
IMPORTED_FLAG="${STATUS_DIR}/imported"
REALM_FILE="/usr/share/java/keycloak/realm-export.json"

# НЕ перезаписываем KC_DB_URL (он приходит из docker-compose.yml)
if [ -z "${KC_DB_URL:-}" ]; then
  echo "ERROR: KC_DB_URL is empty. Check docker-compose.yml (quotation-book-keycloak -> environment -> KC_DB_URL)."
  exit 1
fi

mkdir -p "$STATUS_DIR"

if [ ! -f "$IMPORTED_FLAG" ]; then
  echo "Importing realm configuration..."
  /usr/share/java/keycloak/bin/kc.sh import --file="$REALM_FILE" --features=scripts
  touch "$IMPORTED_FLAG"
  echo "Realm configuration imported successfully"
else
  echo "Realm configuration already imported, skipping import"
fi

echo "Starting Keycloak..."
exec /usr/share/java/keycloak/bin/kc.sh start --optimized
