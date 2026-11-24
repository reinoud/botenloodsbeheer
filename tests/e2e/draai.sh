#!/usr/bin/env bash
# Draait de E2E-tests tegen de lokale stack, via Traefik. Vooraf:
#   docker compose -f docker-compose.yml -f compose.dev.yml up --build -d
# Elke test krijgt een eigen uitnodiging, zodat hij ook los draait (-k).
set -euo pipefail
cd "$(dirname "$0")/../.."
c=(docker compose -f docker-compose.yml -f compose.dev.yml ${DRAAI_OVERRIDE:+-f "$DRAAI_OVERRIDE"})
# Een eigen stack naast de gedeelde: COMPOSE_PROJECT_NAME, KOPPELNET, INSTALLATIE en DRAAI_OVERRIDE=documentatie/gebruikers/compose.doc.yml of, voor een release, tests/e2e/compose.release.yml met RELEASE_TAG (geen poorten naar de host).
# Bij de up van zo'n stack ook API_TOKEN_BESTAND=./secrets/api_token.<project>, vooraf aangemaakt met mode 600 (#368).
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
# #368: zonder API_TOKEN_BESTAND het pad van een installatie, met een waarde dat bestand.
basis=(docker compose --env-file "$dummy" -f docker-compose.yml config)
env -u API_TOKEN_BESTAND "${basis[@]}" | grep -qx "    file: $PWD/secrets/api_token" \
  || { echo "Zonder API_TOKEN_BESTAND is het tokenbestand niet secrets/api_token." >&2; exit 1; }
API_TOKEN_BESTAND=./secrets/api_token.proef "${basis[@]}" \
  | grep -qx "    file: $PWD/secrets/api_token.proef" \
  || { echo "API_TOKEN_BESTAND komt niet in het tokenbestand van compose." >&2; exit 1; }

# De leden komen via de integratiecontainer met de stub (ADR-012), zoals in de
# beheerdocumentatie. Een nieuw token in het bestand dat de container leest (secrets/api_token, of
# API_TOKEN_BESTAND bij de up van een eigen project). De container staat stil terwijl
# er een importverzoek klaarkomt; anders pakt hij het op vóór het log hieronder begint, en
# zonder verzoek importeert hij tussen 00:00 en SYNC_TIJDSTIP niet (#45).
# Na elke run, ook na een mislukte, ruimt tests/e2e/opruimen.sql op wat van een E2E-run is, ook de
# resten van eerdere runs (#142). Eigenaarsrol in de db-container van de dev-stack; de logregels blijven.
opruimen() {
  local rc=$?
  trap - EXIT
  if [ -n "$oorspronkelijk" ]; then  # het e2e-token verdwijnt hieronder uit de db (#374)
    cat "$oorspronkelijk" > "$token_bestand" || { echo "Tokenbestand terugzetten mislukt." >&2; rc=1; }
    "${c[@]}" restart integratie >/dev/null || { echo "Integratiecontainer herstarten mislukt." >&2; rc=1; }
  elif [ "$stil" = 1 ]; then  # een foutroute na 'stop integratie' laat hem anders uit (#223)
    "${c[@]}" start integratie >/dev/null || { echo "Integratiecontainer starten mislukt." >&2; rc=1; }
  fi
  "${c[@]}" exec -T db psql -q -U botenloods -d botenloods -v stempel="$stempel" \
    < tests/e2e/opruimen.sql >/dev/null || { echo "Opruimen van de E2E-gegevens mislukt." >&2; rc=1; }
  rm -f "$dummy" "$fout" "$oorspronkelijk"
  exit $rc
}
stil=0
oorspronkelijk=  # kopie van het tokenbestand tot de run klaar is (#374)
trap opruimen EXIT
# Maakt een robottoken en geeft alleen de waarde; de uitleg op stderr komt alleen bij een fout.
robot() {
  "${c[@]}" exec -T web flask token robot "$@" 2>"$fout" | tail -n 1 \
    || { echo "Token $1 aanmaken mislukt:" >&2; cat "$fout" >&2; return 1; }; }
# Een eigen project mag het token van de dev-stack niet overschrijven (#368): het moet met een eigen
# API_TOKEN_BESTAND gestart zijn, en dat bestand ligt in secrets/ (buiten git en de build context).
container=$("${c[@]}" ps -aq integratie)
token_bestand=$([ -z "$container" ] || docker inspect -f \
  '{{range .Mounts}}{{if eq .Destination "/run/secrets/api_token"}}{{.Source}}{{end}}{{end}}' "$container")
project=$("${c[@]}" config | awk '$1 == "name:" {print $2; exit}')
if [ -z "$token_bestand" ] || [[ "$(realpath "$token_bestand")" != "$(realpath secrets)"/* ]] \
   || { [ "$project" != botenloods ] && [ "$token_bestand" -ef secrets/api_token ]; }; then
  echo "Project $project leest het token uit '$token_bestand' (of heeft geen integratiecontainer)." \
    "Start een eigen project met API_TOKEN_BESTAND=./secrets/api_token.$project (bestand vooraf" \
    "aanmaken, mode 600)." >&2
  exit 1
fi
# Wacht tot Traefik de router van de API heeft. Zonder router geeft Traefik 404, en na één fout
# wacht de integratiecontainer een uur (#368). Een PUT met alleen een te grote Content-Length
# krijgt 413 van de router zelf en bereikt de API niet.
api_router() { "${c[@]}" exec -T integratie python -c 'import http.client, os, urllib.parse
u = urllib.parse.urlsplit(os.environ["API_URL"])
v = http.client.HTTPConnection(u.hostname, u.port, timeout=5)
v.putrequest("PUT", u.path + "/leden"); v.putheader("Content-Length", "3145729"); v.endheaders()
raise SystemExit(v.getresponse().status != 413)' 2>/dev/null; }
for _ in $(seq 60); do api_router && break; sleep 1; done
api_router || { echo "Na 60 seconden geen router naar de API in Traefik (404), of de" \
  "integratiecontainer draait niet." >&2; exit 1; }
oorspronkelijk=$(mktemp)  # mode 600
cat "$token_bestand" > "$oorspronkelijk"
robot "e2e-integratie-$stempel" --recht leden:importeren --recht bootaantallen:lezen \
  > "$token_bestand"
chmod 600 "$token_bestand"
stil=1
"${c[@]}" stop integratie >/dev/null
koppel_ip=$(docker inspect -f '{{range $n, $v := .NetworkSettings.Networks}}{{$n}} {{$v.IPAddress}}
{{end}}' "$("${c[@]}" ps -q traefik)" | awk '$1 ~ /_koppeling$/ {print $2}')
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
            methodes intrekken beheerders kijkers kijkerzelf vrij leden huisstijl import opzeggend bootwijzigen \
            wachtlijst wachtlijstfout kaartjes status bootaantallen tokens tokenscollega \
            tokensintrekken bootsoorten indelingraster rekoverzicht bootplaats rekindelingcsv \
            bezettingcsv bezettingsoort eigenaaronbekend weeronbekend clubboot plaatseigenaar bootverplaatsen zoeken uploadgrens terugnaar lidkoppeling lijstfilter ongeldigeleden passkey overloop oudlid zonderfoto zonderplaats; do
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
  local rc=0
  "${c[@]}" --profile e2e run --rm -e E2E_STEMPEL="$stempel" -e E2E_TOKEN_NIEUW_NAAM="$nieuw" \
    "${links[@]}" "${tokens[@]}" "${tokens_lezen[@]}" e2e pytest -p no:cacheprovider "$@" || rc=$?
  # Na een fout wacht de integratiecontainer een uur en faalt test_import.py; toon dan de oorzaak (#368).
  if "${c[@]}" logs --since "$start" integratie | grep "Import mislukt" >&2; then
    echo "De integratiecontainer meldde een fout tijdens de run. 404's van Traefik op /api/:" >&2
    "${c[@]}" logs --since "$start" traefik | grep ' /api/v1/[^ ]* HTTP/1.1" 404 ' >&2 || true
    start=$(date -u +%Y-%m-%dT%H:%M:%SZ)  # elke fout één keer melden
  fi
  return $rc; }
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
