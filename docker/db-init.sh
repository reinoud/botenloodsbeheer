#!/bin/sh
# Maakt de drie rollen zonder superuser (ADR-006, ADR-012): botenloods_web voor de webapplicatie,
# botenloods_taken voor de worker (mag het log opschonen), botenloods_api voor de API.
# Draait vanzelf bij een lege database. Na een update met een nieuwe rol, of om een wachtwoord
# te wijzigen, opnieuw te draaien met:
#   docker compose exec db sh /docker-entrypoint-initdb.d/rollen.sh
# De rechten op tabellen zet de migratie.
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v web="$DB_WEB_WACHTWOORD" -v taken="$DB_TAKEN_WACHTWOORD" -v api="$DB_API_WACHTWOORD" <<'SQL'
SELECT format('CREATE ROLE %I', rol) FROM unnest(ARRAY['botenloods_web', 'botenloods_taken',
  'botenloods_api']) AS rol WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = rol)\gexec
ALTER ROLE botenloods_web LOGIN PASSWORD :'web';
ALTER ROLE botenloods_taken LOGIN PASSWORD :'taken';
ALTER ROLE botenloods_api LOGIN PASSWORD :'api';
SQL
