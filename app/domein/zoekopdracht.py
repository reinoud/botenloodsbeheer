"""Zoeken vanuit de kop (#154): één term, treffers in boten, leden zonder boot en plaatsen zonder boot.

De term komt van de beheerder en is externe invoer. Hij gaat alleen als parameter naar de
database en nergens naar een log (eis 8 van het ontwerp); de functies hier loggen niets.
"""

from collections import namedtuple

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.domein import leden
from app.models import Boot, Lid, Plaats, Rek, db

MIN_TEKENS = 2
MAX_TEKENS = 100
MAX_TREFFERS = 50

# soort is "boot", "lid" of "plaats"; object is het bijbehorende model. totaal telt ook de
# treffers die niet in treffers staan, omdat er hooguit MAX_TREFFERS worden getoond.
Resultaat = namedtuple("Resultaat", "totaal treffers")


def schoon(term):
    """De term zoals hij gezocht wordt: zonder omringende spaties, hooguit MAX_TEKENS tekens."""
    return (term or "").strip()[:MAX_TEKENS]


def zoek(term):
    """Treffers voor de term, of None als de term te kort is om te zoeken.

    Eerst boten (op naam, dan id), dan leden zonder boot (op naam, dan lidnummer), dan plaatsen
    zonder boot (in loodsvolgorde). Een boot telt als treffer op zijn naam, de naam of het lidnummer
    van de eigenaar of de plaatscode; een lid met een boot is dus alleen via zijn boot te vinden."""
    term = schoon(term)
    if len(term) < MIN_TEKENS:
        return None
    # shortcut: alle treffers worden geladen en daarna afgekapt; bij ongeveer 600 rijen volstaat dat.
    gevonden = db.session.scalars(
        select(Boot).outerjoin(Boot.lid).outerjoin(Boot.plaats)
        .where(or_(leden.bevat(Boot.naam, term), leden.bevat(Lid.naam, term),
                   leden.bevat(Lid.lidnummer, term), leden.bevat(Plaats.code, term)))
        .order_by(Boot.naam, Boot.id)
        .options(selectinload(Boot.lid), selectinload(Boot.plaats), selectinload(Boot.bootsoort))
    ).all()
    zonder_boot = db.session.scalars(
        select(Lid).where(~Lid.boten.any(), or_(leden.bevat(Lid.naam, term), leden.bevat(Lid.lidnummer, term)))
        .order_by(Lid.naam, Lid.lidnummer)
    ).all()
    vrij = db.session.scalars(
        select(Plaats).join(Plaats.rek).where(Plaats.boot_id.is_(None), leden.bevat(Plaats.code, term))
        .order_by(Rek.volgorde, Rek.id, Plaats.verdieping, Plaats.vak)
    ).all()
    alles = ([("boot", b) for b in gevonden] + [("lid", lid) for lid in zonder_boot]
             + [("plaats", p) for p in vrij])
    return Resultaat(len(alles), alles[:MAX_TREFFERS])
