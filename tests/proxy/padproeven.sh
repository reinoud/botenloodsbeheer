#!/usr/bin/env bash
# Padproeven van ADR-013 (gecodeerd pad, padparameters, Host) via een losse Traefik (issue #454).
# Draai na elke andere Traefik-versie of -digest in tests/proxy/compose.traefik.yml, en na een
# wijziging aan de routers van web in docker-compose.yml:
#   tests/proxy/padproeven.sh
# Start web uit docker-compose.yml met zijn eigen labels, met tests/proxy/echo.py als upstream
# (compose.pad.yml), en de losse Traefik uit compose.traefik.yml. Een proef is een aanroep met
# een verwachte uitkomst; elke afwijking telt als fout en geeft exitcode 1.
# Eigen compose-project botenloods-padtest, INSTALLATIE=padtest en eigen subnetten
# 10.213.56-58.0/24; geen poorten op de host, dus de dev-stack en draai.sh blijven ongemoeid.
# Ruimt containers en netwerken altijd op. Bouwt niets: gebruikt botenloods-app zoals het lokaal
# staat. Het script draait niet twee keer tegelijk.
# Vier rondes met telkens een nieuwe Traefik (uit, aan, uit, aan): de opties voor gecodeerde
# tekens staan uit (de standaard van Traefik) of aan (zoals in de beheerdocumentatie), en een
# proef op routering telt pas na drie herstarts (overlay §4, Security en proxy).
# De verwachte uitkomsten zijn die van v3.7.18 (werk/traefik-proeven.md, herhaling v3.7.18).
# Wijkt een andere versie bedoeld af, pas dan de verwachting hieronder aan, met de reden.
set -euo pipefail
cd "$(dirname "$0")/../.."
start=$SECONDS

# Dummywaarden; --env-file /dev/null houdt .env buiten de proef.
export INSTALLATIE=padtest DOMEIN=padtest.invalid BASIS_URL=https://padtest.invalid \
  APP_OMGEVING=productie TRAEFIK_CERTRESOLVER=proef KOPPELNET=10.213.58.0/24 \
  POSTGRES_PASSWORD=proef DB_WEB_WACHTWOORD=proef DB_API_WACHTWOORD=proef \
  DB_TAKEN_WACHTWOORD=proef SECRET_KEY=proef-proef-proef-proef-proef-proef \
  TOTP_SLEUTEL=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
  PROEF_TRAEFIK_KOPPELING=10.213.58.2 PROEF_TRAEFIK_KLANT=10.213.56.2
unset PROEF_PROXYPROTOCOL PROEF_GECODEERD
client=10.213.56.10

c=(docker compose -p botenloods-padtest --env-file /dev/null -f docker-compose.yml
   -f tests/proxy/compose.traefik.yml -f tests/proxy/compose.pad.yml)
netwerken=("$INSTALLATIE"_voorkant "$INSTALLATIE"_koppeling "$INSTALLATIE"_klant)
stack_weg() {
  "${c[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  docker network rm "${netwerken[@]}" >/dev/null 2>&1 || true
}
stack_weg  # resten van een afgebroken run
trap stack_weg EXIT

fouten=()
controle() {  # controle <naam> <commando...>; telt een fout en gaat door
  echo "== $1"
  "${@:2}" || { echo "MISLUKT: $1"; fouten+=("$1"); }
}
opstarten() {  # opstarten <dienst>: steeds een nieuwe container, zonder afhankelijkheden
  local uitvoer
  uitvoer=$("${c[@]}" up -d --wait --no-build --quiet-pull --no-deps --force-recreate "$1" 2>&1) \
    || { echo "$uitvoer" >&2; exit 1; }
}

# klant.py draait in een container met een vast adres, zoals in draai.sh.
klant() {  # klant <argumenten van klant.py...>; PAD en DOMEIN komen uit de omgeving
  docker run --rm --network "$INSTALLATIE"_klant --ip "$client" \
    -e DOEL="$PROEF_TRAEFIK_KLANT:8443" -e SCHEMA=https -e DOMEIN -e PAD -e WACHT="${WACHT:-0}" \
    -v "$PWD/tests/proxy:/proef:ro" --entrypoint python botenloods-app -I /proef/klant.py "$@"
}
# pad <METHODE> <PAD> <code> [<pad bij de upstream>]: bij 200 moet de upstream het pad krijgen
# (standaard onveranderd); bij een andere status moet Traefik zelf antwoorden.
pad() { PAD=$2 klant pad "$1" "$3" "${4:-$2}"; }
rem() { PAD=$2 klant rem "$1" "$3"; }  # rem <METHODE> <PAD> <ja|nee>

docker network create --internal --subnet 10.213.57.0/24 "$INSTALLATIE"_voorkant >/dev/null
docker network create --internal --subnet "$KOPPELNET" "$INSTALLATIE"_koppeling >/dev/null
docker network create --internal --subnet 10.213.56.0/24 "$INSTALLATIE"_klant >/dev/null
echo "== web met echo.py starten"
opstarten web

ronde() {  # ronde <uit|aan>: de opties voor gecodeerde tekens op websecure staan uit of aan
  local opties=$1 gecodeerd=200 p doel
  if [[ $opties == aan ]]; then export PROEF_GECODEERD=false; gecodeerd=400; else unset PROEF_GECODEERD; fi
  echo "== ronde: nieuwe Traefik, opties voor gecodeerde tekens $opties"
  opstarten traefik

  # WACHT=1: wacht tot Traefik de router van web kent. De positieve controles bewijzen dat een
  # gewone aanroep de upstream bereikt en dat de rem op inloggen werkt; zonder die controles
  # bewijst "geen rem" of een 400 niets.
  WACHT=1 controle "[$opties] GET /inloggen bereikt de upstream" pad GET /inloggen 200
  controle "[$opties] POST /inloggen: 429 boven de grens" rem POST /inloggen ja
  controle "[$opties] POST /uitnodiging/x/wachtwoord: 429 boven de grens" \
    rem POST /uitnodiging/x/wachtwoord ja
  controle "[$opties] GET /inloggen valt niet onder de rem" rem GET /inloggen nee
  controle "[$opties] GET /api/v1/ik: de publieke kant kent /api/ niet" pad GET /api/v1/ik 404

  # Gecodeerde tekens (ADR-013 regel 83, issue #65): Traefik kiest de router op het pad zoals
  # het binnenkomt. Met de opties aan geeft Traefik 400; zonder gaat het pad ongewijzigd door.
  for p in /%2Finloggen /%2finloggen/code /%2Fuitnodiging/abc /%5Cinloggen /%00inloggen \
    /%252Finloggen /.%2F /api%2Fv1/ik; do
    # Traefik schrijft de hexcijfers van %2f hoofdletter, maar laat het teken gecodeerd.
    controle "[$opties] GET $p: $gecodeerd" pad GET "$p" $gecodeerd "${p//%2f/%2F}"
  done
  # Zonder de opties valt dit pad onder web en niet onder inloggen: geen rem. Dan is de
  # applicatielaag (400 bij % in RAW_URI) de enige bescherming; echo.py heeft die laag niet.
  if [[ $opties == uit ]]; then
    controle "[uit] POST /%2Finloggen: geen rem" rem POST /%2Finloggen nee
    controle "[uit] POST /%2Fuitnodiging/abc: geen rem" rem POST /%2Fuitnodiging/abc nee
  else
    controle "[aan] POST /%2Finloggen: 400 van Traefik" pad POST /%2Finloggen 400
  fi

  # Traefik decodeert deze tekens zelf voor de routering, in elke stand.
  controle "[$opties] POST /%69nloggen valt onder de rem van inloggen" rem POST /%69nloggen ja
  controle "[$opties] GET /%69nloggen komt als /inloggen binnen" \
    pad GET /%69nloggen 200 /inloggen
  controle "[$opties] GET /%61pi/v1/ik komt als /api/v1/ik: geen router" pad GET /%61pi/v1/ik 404
  controle "[$opties] GET /%2E%2E/inloggen komt als /inloggen binnen" \
    pad GET /%2E%2E/inloggen 200 /inloggen

  # Padparameters en dot-segments (v3.7.18, migratienotitie): Traefik lost ze op voor de
  # routering. Onder v3.7.17 gingen /;a/inloggen en /foo/.;bar/baz ongewijzigd door.
  controle "[$opties] GET /foo/.;bar/baz" pad GET '/foo/.;bar/baz' 200 /foo/baz
  controle "[$opties] GET /foo/..;bar/baz" pad GET '/foo/..;bar/baz' 200 /baz
  controle "[$opties] GET /foo/;bar/baz" pad GET '/foo/;bar/baz' 200 /foo/baz
  controle "[$opties] GET /;a/inloggen komt als /inloggen binnen" \
    pad GET '/;a/inloggen' 200 /inloggen
  controle "[$opties] POST /;a/inloggen valt onder de rem van inloggen" \
    rem POST '/;a/inloggen' ja
  controle "[$opties] GET /api/..;x/inloggen" pad GET '/api/..;x/inloggen' 200 /inloggen
  controle "[$opties] GET /inloggen/..;x/api/v1/ik komt als /api/v1/ik: geen router" \
    pad GET '/inloggen/..;x/api/v1/ik' 404
  controle "[$opties] GET //inloggen" pad GET //inloggen 200 /inloggen
  controle "[$opties] GET /inloggen/./x" pad GET /inloggen/./x 200 /inloggen/x
  # Een padparameter in het laatste segment gaat ongewijzigd door.
  controle "[$opties] GET /api;x/v1/ik" pad GET '/api;x/v1/ik' 200
  controle "[$opties] GET /inloggen;x" pad GET '/inloggen;x' 200

  # Host-matcher (v3.7.18 valideert de waarde): poort, hoofdletters en punt tellen niet mee.
  for doel in padtest.invalid:8443 PADTEST.INVALID padtest.invalid.; do
    DOMEIN=$doel controle "[$opties] Host $doel" pad GET /inloggen 200
  done
  DOMEIN=padtest.invalid%20 controle "[$opties] Host padtest.invalid%20: geen router" \
    pad GET /inloggen 404
}
ronde uit; ronde aan; ronde uit; ronde aan

echo "Klaar in $((SECONDS - start)) s."
if ((${#fouten[@]})); then
  printf 'Mislukte controles (%d):\n' "${#fouten[@]}"; printf '  %s\n' "${fouten[@]}"; exit 1
fi
echo "Alle controles geslaagd."
