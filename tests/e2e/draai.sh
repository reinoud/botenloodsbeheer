#!/usr/bin/env bash
# Draait de E2E-tests tegen de lokale stack. Vooraf:
#   docker compose -f docker-compose.yml -f compose.dev.yml up --build -d
# Elke test krijgt een eigen uitnodiging, zodat hij ook los draait (-k).
set -euo pipefail
cd "$(dirname "$0")/../.."
c=(docker compose -f docker-compose.yml -f compose.dev.yml)
stempel=$(date +%s)

# De leden komen via de integratiecontainer met de stub (ADR-012), zoals in de
# beheerdocumentatie. Een nieuw token in secrets/api_token; na de herstart importeert de
# container meteen, omdat hij nog geen geslaagde import van vandaag kent.
"${c[@]}" exec -T web flask token robot "e2e-integratie-$stempel" --recht leden:importeren \
  --recht bootaantallen:lezen 2>/dev/null | tail -n 1 > secrets/api_token
chmod 600 secrets/api_token
start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"${c[@]}" restart integratie >/dev/null
geimporteerd() { "${c[@]}" logs --since "$start" integratie | grep "Import geslaagd" >/dev/null; }
for _ in $(seq 30); do geimporteerd && break; sleep 2; done
geimporteerd || { echo "De integratiecontainer importeerde niet; zie zijn log." >&2; exit 1; }
"${c[@]}" exec -T worker flask seed  # doet niets als de loods al gegevens heeft

links=()
for soort in passkey wachtwoord vergrendel bezoeker indeling regels plaatsbeheer \
            methodes intrekken beheerders vrij leden huisstijl import opzeggend; do
  link=$("${c[@]}" exec -T web flask beheerder uitnodigen "e2e-$soort-$stempel" | tail -n 1)
  links+=(-e "E2E_LINK_$(tr '[:lower:]' '[:upper:]' <<<"$soort")=$link")
done

# Robottokens voor test_api.py. De e2e-container deelt het netwerk van nginx: 127.0.0.1.
token() { "${c[@]}" exec -T web flask token robot "e2e-$1-$stempel" --recht leden:importeren \
  "${@:2}" 2>/dev/null | tail -n 1; }
# Zonder leden:importeren, voor BLB-032 criterium 2.
tokens_lezen=(-e "E2E_TOKEN_LEZEN=$("${c[@]}" exec -T web flask token robot "e2e-lezen-$stempel" \
  --recht bootaantallen:lezen --whitelist 127.0.0.1/32 2>/dev/null | tail -n 1)")
tokens=(-e "E2E_TOKEN_API=$(token api --whitelist 127.0.0.1/32)"
        -e "E2E_TOKEN_TEMPO=$(token tempo --whitelist 127.0.0.1/32)"
        -e "E2E_TOKEN_PREFIX=$(token prefix --whitelist 127.0.0.1/32)"
        -e "E2E_TOKEN_KOPPELNET=$(token koppelnet)"
        -e "E2E_TOKEN_INGETROKKEN=$(token ingetrokken --whitelist 127.0.0.1/32)"
        -e "E2E_TOKEN_IMPORT=$(token import --whitelist 127.0.0.1/32)")
"${c[@]}" exec -T web flask token intrekken "e2e-ingetrokken-$stempel" >/dev/null

e2e() { "${c[@]}" --profile e2e run --rm -e E2E_STEMPEL="$stempel" "${links[@]}" "${tokens[@]}" \
  "${tokens_lezen[@]}" e2e pytest -p no:cacheprovider "$@"; }

# Nginx staat 20 inlogverzoeken direct toe en daarna 30 per minuut per IP-adres (ADR-001).
# De hele suite blijft daar per bestand onder; tussen de bestanden loopt de teller leeg.
if [ $# -gt 0 ]; then e2e "$@"; exit; fi
status=0
for bestand in tests/e2e/test_*.py; do
  e2e "$(basename "$bestand")" || status=1
  sleep 40
done
exit $status
