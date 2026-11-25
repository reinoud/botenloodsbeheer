#!/usr/bin/env bash
# E2E van het vangnet (#418): stopt web en api op de lokale stack en toetst de 503 van
# documentatie/beheer/voorbeelden/vangnet. De e2e-container heeft geen docker, dus dit script
# stopt en start; tests/e2e/vangnet/test_fase.py toetst per fase. draai.sh roept het aan na de
# suite; los: tests/e2e/vangnet.sh. De stack (zie draai.sh) draait al. Het vangnet draait alleen
# tijdens dit script: de trap start web en api weer en haalt het vangnet weg, ook na een fout.
set -euo pipefail
cd "$(dirname "$0")/../.."
c=(docker compose -f docker-compose.yml -f compose.dev.yml ${DRAAI_OVERRIDE:+-f "$DRAAI_OVERRIDE"})
v=(docker compose -p "${INSTALLATIE:-botenloods}-vangnet" --env-file "${COMPOSE_ENV_FILES:-.env}" -f documentatie/beheer/voorbeelden/vangnet/compose.yml
   -f compose.vangnet.dev.yml)
gezond() { # wacht tot de dienst healthy is
  for _ in $(seq 90); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "$("${c[@]}" ps -q "$1")")" = healthy ] && return 0
    sleep 1
  done
  echo "$1 werd niet healthy." >&2; return 1; }
herstel() {
  local rc=$?
  trap - EXIT
  "${c[@]}" start web api >/dev/null || rc=1
  "${v[@]}" down >/dev/null || rc=1
  gezond web || rc=1
  gezond api || rc=1
  exit $rc
}
trap herstel EXIT
koppel_ip=$(docker inspect -f '{{range $n, $v := .NetworkSettings.Networks}}{{$n}} {{$v.IPAddress}}
{{end}}' "$("${c[@]}" ps -q traefik)" | awk '$1 ~ /_koppeling$/ {print $2}')
fase() {
  "${c[@]}" --profile e2e run --rm -e E2E_STEMPEL=0 -e E2E_VANGNET_FASE="$1" \
    -e E2E_API_URL="http://$koppel_ip:8081/api/v1" e2e pytest -p no:cacheprovider vangnet/test_fase.py; }
"${v[@]}" up -d --wait >/dev/null
fase gewoon
"${c[@]}" stop web >/dev/null
fase web_uit
"${c[@]}" start web >/dev/null; gezond web
"${c[@]}" stop api >/dev/null
fase api_uit
"${c[@]}" start api >/dev/null; gezond api
fase hersteld
