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
for soort in passkey wachtwoord vergrendel bezoeker indeling regels plaatsbeheer \
            methodes intrekken beheerders vrij leden huisstijl; do
  link=$("${c[@]}" exec -T web flask beheerder uitnodigen "e2e-$soort-$stempel" | tail -n 1)
  links+=(-e "E2E_LINK_$(tr '[:lower:]' '[:upper:]' <<<"$soort")=$link")
done

e2e() { "${c[@]}" --profile e2e run --rm -e E2E_STEMPEL="$stempel" "${links[@]}" \
  e2e pytest -p no:cacheprovider "$@"; }

# Nginx staat 20 inlogverzoeken direct toe en daarna 30 per minuut per IP-adres (ADR-001).
# De hele suite blijft daar per bestand onder; tussen de bestanden loopt de teller leeg.
if [ $# -gt 0 ]; then e2e "$@"; exit; fi
status=0
for bestand in tests/e2e/test_*.py; do
  e2e "$(basename "$bestand")" || status=1
  sleep 40
done
exit $status
