#!/bin/sh
# Draait één keer, bij een lege database. Maakt de twee rollen zonder superuser (ADR-006):
# botenloods_web voor de webapplicatie, botenloods_taken voor de worker (mag het log opschonen).
# De rechten op tabellen zet de migratie.
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v web="$DB_WEB_WACHTWOORD" -v taken="$DB_TAKEN_WACHTWOORD" <<'SQL'
CREATE ROLE botenloods_web LOGIN PASSWORD :'web';
CREATE ROLE botenloods_taken LOGIN PASSWORD :'taken';
SQL
