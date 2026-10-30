#!/usr/bin/env bash
# Draait de E2E-tests tegen de lokale stack. Vooraf:
#   docker compose -f docker-compose.yml -f compose.dev.yml up --build -d
set -euo pipefail
cd "$(dirname "$0")/../.."
c=(docker compose -f docker-compose.yml -f compose.dev.yml)
stempel=$(date +%s)

link() { "${c[@]}" exec -T web flask beheerder uitnodigen "e2e-$1-$stempel" | tail -n 1; }

"${c[@]}" --profile e2e run --rm \
  -e E2E_STEMPEL="$stempel" \
  -e E2E_LINK_PASSKEY="$(link passkey)" \
  -e E2E_LINK_WACHTWOORD="$(link wachtwoord)" \
  -e E2E_LINK_VERGRENDEL="$(link vergrendel)" \
  e2e pytest -p no:cacheprovider "$@"
