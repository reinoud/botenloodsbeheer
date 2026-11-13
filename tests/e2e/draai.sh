#!/usr/bin/env bash
# Draait de E2E-tests tegen de lokale stack, via Traefik. Vooraf:
#   docker compose -f docker-compose.yml -f compose.dev.yml up --build -d
# Elke test krijgt een eigen uitnodiging, zodat hij ook los draait (-k).
set -euo pipefail
cd "$(dirname "$0")/../.."
c=(docker compose -f docker-compose.yml -f compose.dev.yml ${DRAAI_OVERRIDE:+-f "$DRAAI_OVERRIDE"})
# Een eigen stack naast de gedeelde: COMPOSE_PROJECT_NAME, KOPPELNET, INSTALLATIE en DRAAI_OVERRIDE=documentatie/gebruikers/compose.doc.yml (geen poorten naar de host).
stempel=$(date +%s)

# BLB-042 criterium 7: compose.api-extern.yml start niet zonder API_EXTERN_BRONNEN, en met een
# waarde komt die in de whitelist van Traefik. Dummywaarden, zodat .env niet meetelt.
dummy=$(mktemp)
fout=$(mktemp)
trap 'rm -f "$dummy" "$fout"' EXIT
for v in BASIS_URL DB_API_WACHTWOORD DB_TAKEN_WACHTWOORD DB_WEB_WACHTWOORD DOMEIN \
         POSTGRES_PASSWORD SECRET_KEY TOTP_SLEUTEL; do echo "$v=x"; done > "$dummy"
extern=(docker compose --env-file "$dummy" -f docker-compose.yml -f compose.api-extern.yml config)
for leeg in "-u API_EXTERN_BRONNEN" "API_EXTERN_BRONNEN="; do
  if env $leeg "${extern[@]}" -q 2>/dev/null; then
    echo "compose.api-extern.yml start zonder API_EXTERN_BRONNEN ($leeg)." >&2; exit 1
  fi
done
API_EXTERN_BRONNEN=192.0.2.0/24 "${extern[@]}" | grep -q "sourcerange: 192.0.2.0/24" \
  || { echo "API_EXTERN_BRONNEN komt niet in de whitelist van Traefik." >&2; exit 1; }

# De leden komen via de integratiecontainer met de stub (ADR-012), zoals in de
# beheerdocumentatie. Een nieuw token in secrets/api_token. De container staat stil terwijl
# er een importverzoek klaarkomt; anders pakt hij het op vóór het log hieronder begint, en
# zonder verzoek importeert hij tussen 00:00 en SYNC_TIJDSTIP niet (#45).
# Na elke run, ook na een mislukte, ruimt tests/e2e/opruimen.sql op wat van een E2E-run is, ook de
# resten van eerdere runs (#142). Eigenaarsrol in de db-container van de dev-stack; de logregels blijven.
opruimen() {
  local rc=$?
  trap - EXIT
  if [ "$stil" = 1 ]; then  # een foutroute na 'stop integratie' laat hem anders uit (#223)
    "${c[@]}" start integratie >/dev/null || { echo "Integratiecontainer starten mislukt." >&2; rc=1; }
  fi
  "${c[@]}" exec -T db psql -q -U botenloods -d botenloods -v stempel="$stempel" \
    < tests/e2e/opruimen.sql >/dev/null || { echo "Opruimen van de E2E-gegevens mislukt." >&2; rc=1; }
  rm -f "$dummy" "$fout"
  exit $rc
}
stil=0
trap opruimen EXIT
# Maakt een robottoken en geeft alleen de waarde; de uitleg op stderr komt alleen bij een fout.
robot() {
  "${c[@]}" exec -T web flask token robot "$@" 2>"$fout" | tail -n 1 \
    || { echo "Token $1 aanmaken mislukt:" >&2; cat "$fout" >&2; return 1; }; }
robot "e2e-integratie-$stempel" --recht leden:importeren --recht bootaantallen:lezen \
  > secrets/api_token
chmod 600 secrets/api_token
stil=1
"${c[@]}" stop integratie >/dev/null
# Een verse stack heeft nog geen leden en de import slaat een nieuw opgezegd lid over (#203, #220):
# importeer die eerst zonder opzegdatums; de container brengt ze daarna aan.
koppel_ip=$(docker inspect -f '{{range $n, $v := .NetworkSettings.Networks}}{{$n}} {{$v.IPAddress}}
{{end}}' "$("${c[@]}" ps -q traefik)" | awk '$1 ~ /_koppeling$/ {print $2}')
aantal_leden=$("${c[@]}" exec -T web python -c 'from app import create_app; from app.domein import leden
with create_app().app_context():
    print(len(leden.alle_leden()))' | tail -n 1) \
  || { echo "Telling van de leden mislukt." >&2; exit 1; }
if [ "$aantal_leden" = 0 ]; then
  eerst=$(robot "e2e-eerst-$stempel" --recht leden:importeren --whitelist "$koppel_ip/32")
  "${c[@]}" --profile e2e run --rm -T -e EERST_API="http://$koppel_ip:8081/api/v1" \
    -e EERST_TOKEN="$eerst" e2e python eerste_import.py >/dev/null \
    || { echo "Eerste import van de leden mislukt." >&2; exit 1; }
fi
"${c[@]}" exec -T web python -c 'from app import create_app; from app.domein import CLI, leden
with create_app().app_context():
    leden.import_aangevraagd() or leden.import_aanvragen(CLI)' \
  || { echo "Importverzoek mislukt." >&2; exit 1; }
start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"${c[@]}" start integratie >/dev/null
stil=0
geimporteerd() { "${c[@]}" logs --since "$start" integratie | grep "Import geslaagd" >/dev/null; }
for _ in $(seq 30); do geimporteerd && break; sleep 2; done
geimporteerd || { echo "De integratiecontainer importeerde niet; zie zijn log." >&2; exit 1; }
"${c[@]}" exec -T worker flask seed  # doet niets als de loods al gegevens heeft

links=()
for soort in wachtwoord vergrendel bezoeker indeling regels plaatsbeheer \
            methodes intrekken beheerders vrij leden huisstijl import opzeggend bootwijzigen \
            wachtlijst wachtlijstfout kaartjes status bootaantallen tokens tokenscollega \
            tokensintrekken bootsoorten indelingraster rekoverzicht bootplaats rekindelingcsv \
            bezettingcsv bezettingsoort eigenaaronbekend weeronbekend clubboot plaatseigenaar bootverplaatsen passkey; do
  link=$("${c[@]}" exec -T web flask beheerder uitnodigen "e2e-$soort-$stempel" | tail -n 1)
  links+=(-e "E2E_LINK_$(tr '[:lower:]' '[:upper:]' <<<"$soort")=$link")
done

# Robottokens voor test_api.py en test_import.py. De e2e-container deelt het netwerk van traefik
# en roept de API aan op het adres van traefik op koppeling (koppel_ip hierboven); dat adres is
# dan ook de afzender.
eigen=(--whitelist "$koppel_ip/32")
token() { robot "e2e-$1-$stempel" --recht leden:importeren "${@:2}"; }
# Zonder leden:importeren, voor BLB-032 criterium 2.
tokens_lezen=(-e "E2E_TOKEN_LEZEN=$(robot "e2e-lezen-$stempel" --recht bootaantallen:lezen \
  "${eigen[@]}")")
# Elk token in een eigen toewijzing: in een array met meer $(...) telt alleen de laatste voor set -e.
tokens=(-e "E2E_API_URL=http://$koppel_ip:8081/api/v1")
for soort in api tempo prefix ingetrokken import; do
  extra=(); [[ $soort == import ]] && extra=(--recht leden:lezen)  # test_import.py telt de bestaande leden
  waarde=$(token "$soort" "${eigen[@]}" "${extra[@]}")
  tokens+=(-e "E2E_TOKEN_$(tr '[:lower:]' '[:upper:]' <<<"$soort")=$waarde")
done
# VERVALST staat alleen 10.203.0.99 toe: het adres dat test_api.py in X-Forwarded-For zet.
waarde=$(token vervalst --whitelist 10.203.0.99/32)
tokens+=(-e "E2E_TOKEN_VERVALST=$waarde")
"${c[@]}" exec -T web flask token intrekken "e2e-ingetrokken-$stempel" >/dev/null
# Verloopt binnen 31 dagen: de waarschuwing op de statuspagina (BLB-037 criterium 5).
robot "e2e-kort-$stempel" --recht bootaantallen:lezen --dagen 10 >/dev/null

# Per aanroep een vers token, zodat test_loods.py het in de nieuwste 50 regels van het technische
# log vindt, los of in de hele suite (BLB-043).
e2e() {
  local nieuw="e2e-nieuw-$stempel-$((++aanroep))"
  robot "$nieuw" --recht bootaantallen:lezen >/dev/null || exit 1  # set -e telt niet achter ||
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
