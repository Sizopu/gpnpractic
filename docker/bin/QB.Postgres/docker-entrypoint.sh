#!/bin/bash

set -e

readonly REQUIRED_ENV_VARS=(
  "POSTGRES_DB_NAME"
  "POSTGRES_DB_USER"
  "POSTGRES_DB_PASSWORD")

main() {
  check_env_vars_set
  
  # Копируем SSL файлы с правильными правами
  setup_ssl_files
  
  init_users_and_db
  init_keycloak_db_and_user
}

check_env_vars_set() {
  for required_env_var in ${REQUIRED_ENV_VARS[@]}; do
    if [[ -z "${!required_env_var}" ]]; then
      echo "Error:
    Environment variable '$required_env_var' not set.
    Make sure you have the following environment variables set:
      ${REQUIRED_ENV_VARS[@]}
Aborting."
      exit 1
    fi
  done
}

setup_ssl_files() {
    echo "Setting up SSL files..."
    
    # Создаем директорию для SSL в PGDATA если её нет
    mkdir -p "$PGDATA/ssl"
    
    # Копируем SSL файлы из /opt/postgres/certs в PGDATA/ssl
    if [ -f /opt/postgres/certs/certificate.crt ]; then
        cp /opt/postgres/certs/certificate.crt "$PGDATA/ssl/server.crt"
        chmod 644 "$PGDATA/ssl/server.crt"
        chown gpn:gpn "$PGDATA/ssl/server.crt"
        echo "Copied SSL certificate to $PGDATA/ssl/server.crt"
    fi
    
    if [ -f /opt/postgres/certs/private.key ]; then
        cp /opt/postgres/certs/private.key "$PGDATA/ssl/server.key"
        chmod 600 "$PGDATA/ssl/server.key"
        chown gpn:gpn "$PGDATA/ssl/server.key"
        echo "Copied SSL private key to $PGDATA/ssl/server.key"
    fi
}

init_users_and_db() {
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL

DO \$$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$POSTGRES_DB_USER') THEN
    CREATE ROLE $POSTGRES_DB_USER WITH LOGIN PASSWORD '$POSTGRES_DB_PASSWORD' SUPERUSER;
  ELSE
    ALTER ROLE $POSTGRES_DB_USER WITH PASSWORD '$POSTGRES_DB_PASSWORD';
  END IF;
END
\$$;

SELECT 'CREATE DATABASE $POSTGRES_DB_NAME
  WITH OWNER = $POSTGRES_DB_USER
       ENCODING = ''UTF-8''
       LC_COLLATE = ''en_US.UTF-8''
       LC_CTYPE = ''en_US.UTF-8''
       CONNECTION LIMIT = -1
       TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB_NAME')\gexec

\c $POSTGRES_DB_NAME;

COMMENT ON DATABASE $POSTGRES_DB_NAME IS 'База данных управления миграциями БД';
ALTER DATABASE $POSTGRES_DB_NAME SET TIME ZONE 'Europe/Moscow';

GRANT ALL ON DATABASE $POSTGRES_DB_NAME TO $POSTGRES_DB_USER;
REVOKE ALL ON DATABASE $POSTGRES_DB_NAME FROM PUBLIC;
REVOKE CREATE ON SCHEMA PUBLIC FROM PUBLIC;

CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "tablefunc";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL
}

init_keycloak_db_and_user() {
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOF

DO \$$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$KEYCLOAK_DB_USER') THEN
    CREATE ROLE $KEYCLOAK_DB_USER WITH LOGIN PASSWORD '$KEYCLOAK_DB_PASSWORD' SUPERUSER;
  ELSE
    ALTER ROLE $KEYCLOAK_DB_USER WITH PASSWORD '$KEYCLOAK_DB_PASSWORD';
  END IF;
END
\$$;

SELECT 'CREATE DATABASE $KEYCLOAK_DB_NAME
  WITH OWNER = $KEYCLOAK_DB_USER
       ENCODING = ''UTF-8''
       LC_COLLATE = ''en_US.UTF-8''
       LC_CTYPE = ''en_US.UTF-8''
       CONNECTION LIMIT = -1
       TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$KEYCLOAK_DB_NAME')\gexec

\c $KEYCLOAK_DB_NAME;

COMMENT ON DATABASE $KEYCLOAK_DB_NAME IS 'База данных под Keycloak';
ALTER DATABASE $KEYCLOAK_DB_NAME SET TIME ZONE 'Europe/Moscow';

GRANT ALL ON DATABASE $KEYCLOAK_DB_NAME TO $KEYCLOAK_DB_USER;
REVOKE ALL ON DATABASE $KEYCLOAK_DB_NAME FROM PUBLIC;
REVOKE CREATE ON SCHEMA PUBLIC FROM PUBLIC;
EOF
}

# Добавляем SSL конфигурацию только если SSL файлы существуют
if [ -f "$PGDATA/ssl/server.crt" ] && [ -f "$PGDATA/ssl/server.key" ]; then
    echo "Configuring SSL in postgresql.conf..."
    {
        echo ""
        echo "# SSL Configuration"
        echo "ssl = on"
        echo "ssl_cert_file = '$PGDATA/ssl/server.crt'"
        echo "ssl_key_file = '$PGDATA/ssl/server.key'"
        if [ -n "$POSTGRES_CA_CERT" ] && [ -f "$POSTGRES_CA_CERT" ]; then
            echo "ssl_ca_file = '${POSTGRES_CA_CERT}'"
        fi
        echo "ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'"
    } >> "$PGDATA/postgresql.conf"
    
    echo "Configuring SSL in pg_hba.conf..."
    {
        echo ""
        echo "# SSL connections"
        echo "hostssl $POSTGRES_DB_NAME $POSTGRES_DB_USER 0.0.0.0/0 trust"
    } >> "$PGDATA/pg_hba.conf"
else
    echo "SSL files not found, PostgreSQL will run without SSL"
fi

main "$@"