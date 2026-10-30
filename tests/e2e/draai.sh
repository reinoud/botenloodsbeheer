#!/usr/bin/env bash
# Draait de E2E-tests tegen de lokale stack. Vooraf:
#   docker compose -f docker-compose.yml -f compose.dev.yml up --build -d
# Elke test krijgt een eigen uitnodiging, zodat hij ook los draait (-k).
set -euo pipefail
cd "$(dirname "$0")/../.."
c=(docker compose -f docker-compose.yml -f compose.dev.yml)
stempel=$(date +%s)

"${c[@]}" exec -T worker flask seed  # doet niets als de loods al gegevens heeft

links=()
for soort in passkey wachtwoord vergrendel bezoeker indeling regels; do
  link=$("${c[@]}" exec -T web flask beheerder uitnodigen "e2e-$soort-$stempel" | tail -n 1)
  links+=(-e "E2E_LINK_$(tr '[:lower:]' '[:upper:]' <<<"$soort")=$link")
done

"${c[@]}" --profile e2e run --rm -e E2E_STEMPEL="$stempel" "${links[@]}" \
  e2e pytest -p no:cacheprovider "$@"
