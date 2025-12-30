#!/bin/bash

set -eu -o pipefail

if [[ $POSTGRES_DB_CONNECTION_ENCRYPT = 'true' ]]; then 
  export POSTGRES_DB_CONNECTION_ENCRYPT_FLAG='-e'
else
  export POSTGRES_DB_CONNECTION_ENCRYPT_FLAG=''
fi

export MIGRATE_ARGS="\
  -d postgres \
  -s /migrations \
  -t ${POSTGRES_DB_HOST}:${POSTGRES_DB_PORT} \
  -u ${POSTGRES_DB_USER}:${POSTGRES_DB_PASSWORD} \
  -yv \
  $POSTGRES_DB_CONNECTION_ENCRYPT_FLAG"

unset POSTGRES_DB_CONNECTION_ENCRYPT_FLAG

exec $@
