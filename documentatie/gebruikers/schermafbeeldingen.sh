#!/usr/bin/env bash
# Maakt alle schermafbeeldingen van de handleiding opnieuw, in documentatie/gebruikers/afbeeldingen/.
# Het script start een eigen stack (project botenloods-doc) met een lege database, vult die met de
# synthetische loods uit flask seed en ruimt alles weer op. De lokale stack blijft ongemoeid.
# Vooraf: het image botenloods-app en een .env. Het image botenloods-e2e (dat van de lokale stack)
# bouwt compose zo nodig en blijft na afloop staan.
set -euo pipefail
cd "$(dirname "$0")/../.."
export KOPPELNET=10.203.77.0/24   # botst anders met het vaste subnet van de lokale stack
export INSTALLATIE=botenloods-doc  # eigen netwerken, routers en een eigen Traefik (ADR-013)
c=(docker compose -p botenloods-doc -f docker-compose.yml -f compose.dev.yml
   -f documentatie/gebruikers/compose.doc.yml)
trap '"${c[@]}" --profile e2e down -v --remove-orphans >/dev/null 2>&1' EXIT

"${c[@]}" up -d --wait db web api worker traefik
flask() { "${c[@]}" exec -T web flask "$@" 2>/dev/null | tail -n 1; }
e2e() { "${c[@]}" --profile e2e run --rm -T "${@:2}" e2e python /documentatie/gebruikers/schermafbeeldingen.py "$1"; }

# Tokens en links gaan alleen via de omgeving van de container, niet naar het scherm. De
# container deelt het netwerk van traefik en roept de API aan op diens adres op koppeling.
koppel_ip=$(docker inspect -f '{{range $n, $v := .NetworkSettings.Networks}}{{$n}} {{$v.IPAddress}}
{{end}}' "$("${c[@]}" ps -q traefik)" | awk '$1 ~ /_koppeling$/ {print $2}')
api=(-e "DOC_API=http://$koppel_ip:8081/api/v1")
token=$(flask token robot doc-import --recht leden:importeren --whitelist "$koppel_ip/32")
# Verloopt binnen 31 dagen: de waarschuwing op de statuspagina (BLB-037).
flask token robot integratie-oud --recht bootaantallen:lezen --dagen 20 >/dev/null
e2e eerst -e "DOC_TOKEN=$token" "${api[@]}"   # een verse stack: de oud-leden komen er pas bij de tweede import in (#220)
e2e import -e "DOC_TOKEN=$token" "${api[@]}"
"${c[@]}" exec -T worker flask seed
# Drie leden met een boot op een plaats krijgen een opzegdatum in de toekomst.
opzeggers=$("${c[@]}" exec -T web python -c "
from app import create_app
from app.models import Boot, Lid, db
from sqlalchemy import select
with create_app().app_context():
    print(','.join(db.session.scalars(select(Lid.lidnummer).join(Boot).where(
        Boot.plaats.has(), Lid.opzegdatum.is_(None)).order_by(Lid.lidnummer).limit(3))))
" 2>/dev/null | tail -n 1)
e2e opzeggers -e "DOC_TOKEN=$token" -e "DOC_OPZEGGERS=$opzeggers" "${api[@]}"

[ -n "${DOC_BREEDTE:-}" ] || rm -f documentatie/gebruikers/afbeeldingen/*.png  # een eigen breedte is voor controle en laat de handleiding staan
link=$(flask beheerder uitnodigen beheerder.een)
e2e schermen -e "DOC_LINK=$link" -e DOC_BREEDTE -e DOC_UIT
ls documentatie/gebruikers/afbeeldingen | wc -l | xargs echo "Schermafbeeldingen gemaakt:"
