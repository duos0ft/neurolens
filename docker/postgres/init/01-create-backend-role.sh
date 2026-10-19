#!/bin/sh
set -eu

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -v backend_password="$NEUROLENS_DB_PASSWORD" <<'SQL'

SELECT format(
    'CREATE ROLE neurolens_admin LOGIN NOBYPASSRLS PASSWORD %L',
    :'backend_password'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = 'neurolens_admin'
)
\gexec

SQL