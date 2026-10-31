#!/usr/bin/env bash
# Maakt alle schermafbeeldingen van de handleiding opnieuw, in documentatie/gebruikers/afbeeldingen/.
# Het script start een eigen stack (project botenloods-doc) met een lege database, vult die met de
# synthetische loods uit flask seed en ruimt alles weer op. De lokale stack blijft ongemoeid.
# Vooraf: de images botenloods-app en botenloods-e2e (docker compose ... build e2e) en een .env.
set -euo pipefail
cd "$(dirname "$0")/../.."
export KOPPELNET=10.203.77.0/24   # botst anders met het vaste subnet van de lokale stack
c=(docker compose -p botenloods-doc -f docker-compose.yml -f compose.dev.yml
   -f documentatie/gebruikers/compose.doc.yml)
trap '"${c[@]}" --profile e2e down -v --remove-orphans >/dev/null 2>&1' EXIT

"${c[@]}" up -d --wait db web api worker nginx
flask() { "${c[@]}" exec -T web flask "$@" 2>/dev/null | tail -n 1; }
e2e() { "${c[@]}" --profile e2e run --rm -T "${@:2}" e2e python /documentatie/gebruikers/schermafbeeldingen.py "$1"; }

# Tokens en links gaan alleen via de omgeving van de container, niet naar het scherm.
token=$(flask token robot doc-import --recht leden:importeren --whitelist 127.0.0.1/32)
e2e import -e "DOC_TOKEN=$token"
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
e2e opzeggers -e "DOC_TOKEN=$token" -e "DOC_OPZEGGERS=$opzeggers"

rm -f documentatie/gebruikers/afbeeldingen/*.png
link=$(flask beheerder uitnodigen beheerder.een)
e2e schermen -e "DOC_LINK=$link"
ls documentatie/gebruikers/afbeeldingen | wc -l | xargs echo "Schermafbeeldingen gemaakt:"
