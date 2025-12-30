#!/bin/bash
set -e
set -x
source .venv/bin/activate
POSTGRES_HOST=${DB_HOST:-postgres}
POSTGRES_PORT=${DB_PORT:-5432}

DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT:-3}
MAX_DB_WAIT_TIME=${MAX_DB_WAIT_TIME:-60}
CUR_DB_WAIT_TIME=0

function get_command_by_name {
  case "$1" in
      backend)
        echo "Check volumes [ static images ] in /opt/app-root/src/static"
        ls -la /opt/app-root/src/static
        command="poetry run python3 backend.py"
        ;;
      worker)
        command="poetry run python3 worker.py"
        ;;
      collectstatic)
        command="poetry run python3 backend.py collectstatic"
        ;;
      collectminio)
        command="poetry run python3 backend.py collectminio"
        ;;
      *)
        echo "usage: $0 [backend|collectstatic|worker]"
        exit 1
  esac
}

postgres_ready_shell(){
  nc -w 1  -v -z "$(getent hosts ${POSTGRES_HOST} | awk '{ print $1 ; exit }')" ${POSTGRES_PORT}
}

if [ $COMMIT_SHA ]; then
  echo "commit_sha of build: ${COMMIT_SHA}"
fi

if ! [ $POSTGRES_READY_CHECK_DISABLE ]; then
    while ! postgres_ready_shell && [ "${CUR_DB_WAIT_TIME}" -lt "${MAX_DB_WAIT_TIME}" ]; do
      echo "⏳ Waiting on DB ${POSTGRES_HOST}:${POSTGRES_PORT}... (${CUR_DB_WAIT_TIME}s / ${MAX_DB_WAIT_TIME}s)"
      sleep "${DB_WAIT_TIMEOUT}"
      CUR_DB_WAIT_TIME=$((CUR_DB_WAIT_TIME + DB_WAIT_TIMEOUT))
    done
fi

if [ "${CUR_DB_WAIT_TIME}" -ge "${MAX_DB_WAIT_TIME}" ]; then
  echo "❌ Waited ${MAX_DB_WAIT_TIME}s or more for the DB to become ready."
  exit 1
fi

not_last_commands=${*%${!#}}
for command_name in $not_last_commands
do
    get_command_by_name "$command_name"
    eval "$command"
done

last_command_name="${@:$#}"
get_command_by_name "$last_command_name"
exec $command