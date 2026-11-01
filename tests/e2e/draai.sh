#!/usr/bin/env bash
# Draait de E2E-tests tegen de lokale stack, via Traefik. Vooraf:
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

# Robottokens voor test_api.py en test_import.py. De e2e-container deelt het netwerk van traefik
# en roept de API aan op het adres van traefik op koppeling; dat adres is dan ook de afzender.
koppel_ip=$(docker inspect -f '{{range $n, $v := .NetworkSettings.Networks}}{{$n}} {{$v.IPAddress}}
{{end}}' "$("${c[@]}" ps -q traefik)" | awk '$1 ~ /_koppeling$/ {print $2}')
eigen=(--whitelist "$koppel_ip/32")
token() { "${c[@]}" exec -T web flask token robot "e2e-$1-$stempel" --recht leden:importeren \
  "${@:2}" 2>/dev/null | tail -n 1; }
# Zonder leden:importeren, voor BLB-032 criterium 2.
tokens_lezen=(-e "E2E_TOKEN_LEZEN=$("${c[@]}" exec -T web flask token robot "e2e-lezen-$stempel" \
  --recht bootaantallen:lezen "${eigen[@]}" 2>/dev/null | tail -n 1)")
# VERVALST staat alleen 10.203.0.99 toe: het adres dat test_api.py in X-Forwarded-For zet.
tokens=(-e "E2E_API_URL=http://$koppel_ip:8081/api/v1"
        -e "E2E_TOKEN_API=$(token api "${eigen[@]}")"
        -e "E2E_TOKEN_TEMPO=$(token tempo "${eigen[@]}")"
        -e "E2E_TOKEN_PREFIX=$(token prefix "${eigen[@]}")"
        -e "E2E_TOKEN_VERVALST=$(token vervalst --whitelist 10.203.0.99/32)"
        -e "E2E_TOKEN_INGETROKKEN=$(token ingetrokken "${eigen[@]}")"
        -e "E2E_TOKEN_IMPORT=$(token import "${eigen[@]}")")
"${c[@]}" exec -T web flask token intrekken "e2e-ingetrokken-$stempel" >/dev/null

# Per aanroep een vers token, zodat test_loods.py het in de nieuwste 50 regels van het technische
# log vindt, los of in de hele suite (BLB-043).
e2e() {
  local nieuw="e2e-nieuw-$stempel-$((++aanroep))"
  "${c[@]}" exec -T web flask token robot "$nieuw" --recht bootaantallen:lezen >/dev/null 2>&1
  "${c[@]}" --profile e2e run --rm -e E2E_STEMPEL="$stempel" -e E2E_TOKEN_NIEUW_NAAM="$nieuw" \
    "${links[@]}" "${tokens[@]}" "${tokens_lezen[@]}" e2e pytest -p no:cacheprovider "$@"; }
aanroep=0

# Traefik staat 20 inlogverzoeken direct toe en daarna 30 per minuut per IP-adres (ADR-001).
# De hele suite blijft daar per bestand onder; tussen de bestanden loopt de teller leeg.
if [ $# -gt 0 ]; then e2e "$@"; exit; fi
status=0
for bestand in tests/e2e/test_*.py; do
  e2e "$(basename "$bestand")" || status=1
  sleep 40
done
exit $status
