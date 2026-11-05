#!/usr/bin/env bash
# Proef van de API van buiten via een losse Traefik (issue #53, ADR-013, BLB-042). Draai na elke
# wijziging aan de labels van api, aan compose.api-extern.yml of aan de eisen aan Traefik:
#   tests/proxy/draai.sh
# Start db, migrate en api uit docker-compose.yml met compose.api-extern.yml, en een losse Traefik
# uit tests/proxy/compose.traefik.yml. Upstream is de echte api: de 401 komt van de whitelist van
# het token in de applicatie. Clients draaien in containers met een vast adres.
#
# Images: bouwt niets. Gebruikt botenloods-app zoals het lokaal staat (bouw het eerst als app/ is
# gewijzigd), postgres:17 en traefik:v3.7.17 op de digest uit de compose-bestanden; laat ze staan.
# Eigen compose-project botenloods-proxytest, INSTALLATIE=proxytest en eigen subnetten
# 10.213.53-55.0/24; raakt de dev-stack niet. Ruimt containers, volume en netwerken altijd op.
# EXTERN_BESTAND kiest een ander bestand dan compose.api-extern.yml (voor een mutant).
# Tweede ronde (issue #54): dezelfde Traefik met proxyprotocol.trustedips op websecure; een client
# speelt load balancer en stuurt het clientadres in een PROXY v1-kop vóór de TLS.
set -euo pipefail
# Alleen de tweede ronde zet de optie; een waarde uit de shell mag ronde 1 niet raken.
unset PROEF_PROXYPROTOCOL
cd "$(dirname "$0")/../.."
start=$SECONDS
extern=${EXTERN_BESTAND:-compose.api-extern.yml}

# Dummywaarden; --env-file /dev/null houdt .env buiten de proef.
export INSTALLATIE=proxytest DOMEIN=proxytest.invalid BASIS_URL=https://proxytest.invalid \
  APP_OMGEVING=productie TRAEFIK_CERTRESOLVER=proef KOPPELNET=10.213.55.0/24 \
  POSTGRES_PASSWORD=proef DB_WEB_WACHTWOORD=proef DB_API_WACHTWOORD=proef \
  DB_TAKEN_WACHTWOORD=proef SECRET_KEY=proef-proef-proef-proef-proef-proef \
  TOTP_SLEUTEL=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
  PROEF_TRAEFIK_KOPPELING=10.213.55.2 PROEF_TRAEFIK_KLANT=10.213.53.2 \
  API_EXTERN_BRONNEN=10.213.53.0/27
toegestaan=10.213.53.10   # in API_EXTERN_BRONNEN en in de whitelist van het token
bron=10.213.53.20         # in API_EXTERN_BRONNEN, niet in de whitelist van het token
vreemd=10.213.53.40       # buiten API_EXTERN_BRONNEN
koppel=10.213.55.10       # op koppeling, voor de positieve controle op intern
koppel2=10.213.55.11      # tweede adres op koppeling, voor de eigen teller in iprem
lb=10.213.53.30           # load balancer in de tweede ronde; in de bronnen, niet in de tokenwhitelist
rem=10.213.53.21          # clientadres voor de proef op iprem in de tweede ronde

c=(docker compose -p botenloods-proxytest --env-file /dev/null -f docker-compose.yml
   -f tests/proxy/compose.traefik.yml)
netwerken=("$INSTALLATIE"_voorkant "$INSTALLATIE"_koppeling "$INSTALLATIE"_klant)
stack_weg() {
  docker rm -f botenloods-proxytest-sein >/dev/null 2>&1 || true
  "${c[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  docker network rm "${netwerken[@]}" >/dev/null 2>&1 || true
}
stack_weg  # resten van een afgebroken run
fout=$(mktemp)
seinmap=$(mktemp -d)  # voor het sein tussen twee clients op intern
chmod 1777 "$seinmap"  # sticky: een andere gebruiker kan het sein niet vervangen
trap 'stack_weg; rm -rf "$fout" "$seinmap"' EXIT

fouten=()
controle() {  # controle <naam> <commando...>; telt een fout en gaat door
  echo "== $1"
  "${@:2}" || { echo "MISLUKT: $1"; fouten+=("$1"); }
}

# Een aanroep vanuit een container met een vast adres; het token gaat via de omgeving.
klant() {  # klant <netwerk> <adres> <doel> <schema> <token> <argumenten van klant.py...>
  TOKEN=$5 docker run --rm --network "$1" --ip "$2" -e DOEL="$3" -e SCHEMA="$4" -e DOMEIN \
    -e TOKEN -e WACHT="${WACHT:-0}" -e PAD -e PROXY -e ANDER -e SEIN \
    -v "$PWD/tests/proxy:/proef:ro" -v "$seinmap:/sein" --entrypoint python \
    botenloods-app -I /proef/klant.py "${@:6}"
}
buiten() { klant "$INSTALLATIE"_klant "$1" "$PROEF_TRAEFIK_KLANT:8443" https "${@:2}"; }
# via_lb <clientadres> <token> <argumenten...>: aanroep van de load balancer met een PROXY-kop.
via_lb() { PROXY=$1 buiten "$lb" "${@:2}"; }
intern() { klant "$INSTALLATIE"_koppeling "$1" "$PROEF_TRAEFIK_KOPPELING:8081" http "${@:2}"; }

# Compose start niet zonder API_EXTERN_BRONNEN, en de waarde komt in de whitelist van Traefik.
config_extern() {
  local leeg
  for leeg in "-u API_EXTERN_BRONNEN" "API_EXTERN_BRONNEN="; do
    if env $leeg "${c[@]}" -f "$extern" config -q 2>/dev/null; then
      echo "FOUT compose start zonder API_EXTERN_BRONNEN ($leeg)"; return 1
    fi
  done
  "${c[@]}" -f "$extern" config | grep -q "sourcerange: $API_EXTERN_BRONNEN" \
    || { echo "FOUT API_EXTERN_BRONNEN staat niet in de whitelist van Traefik"; return 1; }
  echo "OK  zonder API_EXTERN_BRONNEN start compose niet; met waarde staat hij in de whitelist"
}
controle "compose zonder API_EXTERN_BRONNEN" config_extern

docker network create --internal --subnet 10.213.54.0/24 "$INSTALLATIE"_voorkant >/dev/null
docker network create --internal --subnet "$KOPPELNET" "$INSTALLATIE"_koppeling >/dev/null
docker network create --internal --subnet 10.213.53.0/24 "$INSTALLATIE"_klant >/dev/null

echo "== stack starten met $extern"
"${c[@]}" -f "$extern" up -d --wait --no-build --quiet-pull db migrate api traefik 2>"$fout" \
  || { cat "$fout" >&2; exit 1; }

# Robottokens via web (die rol mag tokens maken); geen container voor Traefik (enable=false).
robot() {
  "${c[@]}" run --rm --no-deps -l traefik.enable=false web flask token robot "$@" \
    --recht bootaantallen:lezen 2>"$fout" | tail -n 1 \
    || { echo "Token $1 aanmaken mislukt:" >&2; cat "$fout" >&2; return 1; }
}
token_a=$(robot proxytest-a --whitelist "$toegestaan/32")
token_tempo=$(robot proxytest-tempo --whitelist "$toegestaan/32")
for t in "$token_a" "$token_tempo"; do
  [[ $t == blb_* ]] || { echo "Token aanmaken gaf geen token:" >&2; cat "$fout" >&2; exit 1; }
done

# WACHT=1: de eerste aanroep wacht tot Traefik de router kent.
WACHT=1 controle "200 vanaf een adres in de bronnen en in de tokenwhitelist" \
  buiten "$toegestaan" "$token_a" 200
controle "401 buiten de tokenwhitelist, ook met vervalste koppen" \
  buiten "$bron" "$token_a" 401 - "X-Forwarded-For: $toegestaan" "X_Forwarded_For: $toegestaan" \
  "X-Real-Ip: $toegestaan" "Forwarded: for=$toegestaan"
controle "403 buiten API_EXTERN_BRONNEN" buiten "$vreemd" "$token_a" 403
# Een gecodeerd pad mag niet langs externtoegang (overlay §4, issue #127).
PAD=/api/v1/%2Fik controle "gecodeerd pad buiten API_EXTERN_BRONNEN" \
  buiten "$vreemd" "$token_a" 400,403
controle "429 boven de grens per token" buiten "$toegestaan" "$token_tempo" tempo

echo "== api opnieuw zonder $extern"
"${c[@]}" up -d --wait --no-build --quiet-pull api 2>"$fout" || { cat "$fout" >&2; exit 1; }
# Eerst intern via koppeling: de 401 van de applicatie toont dat Traefik api weer kent.
WACHT=1 controle "intern bereikt api (positieve controle voor de 404)" intern "$koppel" "" 401
controle "404 op websecure zonder $extern" buiten "$toegestaan" "$token_a" 404

# Tweede ronde. Traefik krijgt een nieuwe container, dus elke teller begint leeg.
export PROEF_PROXYPROTOCOL=--entrypoints.websecure.proxyprotocol.trustedips=$lb/32
echo "== tweede ronde: Traefik met proxyprotocol.trustedips=$lb/32, api met $extern"
"${c[@]}" -f "$extern" up -d --wait --no-build --quiet-pull api traefik 2>"$fout" \
  || { cat "$fout" >&2; exit 1; }
# Elke 401 en 403 hieronder volgt het adres uit de PROXY-kop, niet dat van de load balancer.
WACHT=1 controle "LB: 200 voor een clientadres in de bronnen en in de tokenwhitelist" \
  via_lb "$toegestaan" "$token_a" 200
controle "LB: 401 van de applicatie voor een clientadres buiten de tokenwhitelist" \
  via_lb "$bron" "$token_a" 401 - "X-Forwarded-For: $toegestaan"
controle "LB: 403 van Traefik voor een clientadres buiten API_EXTERN_BRONNEN" \
  via_lb "$vreemd" "$token_a" 403
PAD=/api/v1/%2Fik controle "LB: gecodeerd pad voor een clientadres buiten API_EXTERN_BRONNEN" \
  via_lb "$vreemd" "$token_a" 400,403
ANDER=$bron controle "LB: iprem telt per clientadres, ook op het pad met %2F" \
  via_lb "$rem" "" iprem
# Traefik vertrouwt de kop alleen van lb; van een ander adres telt het verbindingsadres.
PROXY=$toegestaan controle "PROXY-kop van $bron, buiten trustedips: 401 op het eigen adres" \
  buiten "$bron" "$token_a" 401
PROXY=$toegestaan controle "PROXY-kop van $vreemd, buiten trustedips: 403 op het eigen adres" \
  buiten "$vreemd" "$token_a" 403

# intern heeft geen PROXY protocol: iprem telt daar per adres op koppeling, zoals zonder de optie.
# Het tweede adres wacht in een eigen container op het sein van het eerste.
intern_iprem() {
  local a=0 b
  docker run -d --name botenloods-proxytest-sein --network "$INSTALLATIE"_koppeling --ip "$koppel2" \
    -e DOEL="$PROEF_TRAEFIK_KOPPELING:8081" -e SCHEMA=http -e DOMEIN -e SEIN=/sein/tijd \
    -v "$PWD/tests/proxy:/proef:ro" -v "$seinmap:/sein" --entrypoint python botenloods-app \
    -I /proef/klant.py sein >/dev/null
  SEIN=/sein/tijd intern "$koppel" "" iprem || a=1
  b=$(docker wait botenloods-proxytest-sein)
  docker logs botenloods-proxytest-sein
  docker rm botenloods-proxytest-sein >/dev/null
  # Een lege b (container niet gestart) telt als fout, niet als 0.
  ((a == 0)) && [[ $b == 0 ]]
}
controle "intern met de optie: 429 na 50 vanaf één adres, 401 voor een tweede adres" intern_iprem

echo "Klaar in $((SECONDS - start)) s."
if ((${#fouten[@]})); then
  printf 'Mislukte controles:\n'; printf '  %s\n' "${fouten[@]}"; exit 1
fi
echo "Alle controles geslaagd."
