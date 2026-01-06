#! /bin/sh

set -eu

VERSION="alpha"
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U "${POSTGRES_USER}" -w -f "./versions/${VERSION}.sql"
