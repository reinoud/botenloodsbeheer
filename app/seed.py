"""flask seed: een synthetische loods op de omvang van de vereniging (architectuur §6.3).

Vaste random seed, dus elke run levert hetzelfde op. Alle gegevens zijn verzonnen.
Afwijkingen van §6.3: seed draait in de worker en importeert geen leden. De leden komen uit
tests/fixtures/leden.json via de integratiecontainer met de stub en PUT /api/v1/leden, de enige
route die leden schrijft (ADR-012); seed weigert zonder leden. Wachtlijst en kleuren volgen met
hun slice. Het testlogo komt niet uit seed maar uit compose.dev.yml (ADR-008).
"""

import random

from flask import current_app
from sqlalchemy import select

from app.domein import CLI, Regelfout, boten, indeling, leden, log, toewijzing
from app.models import Boot, Instelling, Lid, Plaats, Rek, db

VERENIGING = "Kanovereniging De Voorbeeldplas"
# Per rek de bootsoorten die passen; het laatste rek heeft acht clubplaatsen.
REKKEN = {
    "A": ("Kajak", "Surfski"), "B": ("Kajak", "Surfski"), "C": ("Kajak", "Surfski"),
    "D": ("Kajak", "C11"), "E": ("Kajak", "C11"), "F": ("Canadese kano",),
    "G": ("Canadese kano",), "H": ("Supboard", "Kajak"), "I": ("Kajak", "Surfski", "C11"),
    "J": ("Kajak", "Canadese kano"),
}
PLAATSEN_PER_REK = 16
CLUBPLAATSEN = 8
SOORTEN = ("Kajak",) * 5 + ("Surfski", "Canadese kano") * 2 + ("C11", "Supboard")
NAMEN = ("Zeemeeuw", "Waterhoen", "Fuut", "Reiger", "IJsvogel", "Snoek", "Otter", "Bever",
         "Libel", "Golfje", "Stroom", "Kroos")
BOTEN_LEDEN = 170
BOTEN_OUD_LID = 4
CLUBBOTEN = 6
MET_PLAATS = 150


class SeedFout(Exception):
    pass


def seed(echo=print):
    if current_app.config["APP_OMGEVING"] == "productie":
        raise SeedFout("flask seed draait niet in productie.")
    if db.session.scalar(select(Rek).limit(1)):
        echo("De loods heeft al gegevens; seed doet niets.")
        return
    if not db.session.scalar(select(Lid).limit(1)):
        raise SeedFout("Er zijn nog geen leden. Laat eerst de integratiecontainer met de stub "
                       "importeren (documentatie/beheer/integratiecontainer.md).")
    r = random.Random(2026)

    if db.session.get(Instelling, "naam") is None:
        db.session.add(Instelling(sleutel="naam", waarde=VERENIGING))
        log.schrijf(CLI, "instelling.gewijzigd", ["instelling:huisstijl"], {"naam": VERENIGING})
    db.session.commit()

    soort = {s.naam: s.id for s in indeling.bootsoorten()}
    for letter, passend in REKKEN.items():
        rek = indeling.rek_aanmaken(f"Rek {letter}", CLI)
        for n in range(1, PLAATSEN_PER_REK + 1):
            club = letter == "J" and n > PLAATSEN_PER_REK - CLUBPLAATSEN
            indeling.plaats_aanmaken(rek.id, f"{letter}{n:02d}", [soort[s] for s in passend],
                                     club, CLI)

    def boot(eigenaar, oud_lid=False):
        naam = f"{r.choice(NAMEN)} {r.randint(1, 99)}"
        if oud_lid:
            # De boot bestond al voor de opzegging; boot_aanmaken weigert een oud-lid.
            b = Boot(naam=naam, bootsoort_id=soort[r.choice(SOORTEN)], lid_id=eigenaar)
            db.session.add(b)
            db.session.flush()
            log.schrijf(CLI, "boot.aangemaakt", [f"boot:{b.id}", f"lid:{eigenaar}"],
                        {"naam": naam, "bootsoort": b.bootsoort.naam, "clubboot": False,
                         "foto": False, "seed": "oud-lid"})  # #10: ook deze mutatie in het log
            db.session.commit()
            return b
        return boten.boot_aanmaken(naam, soort[r.choice(SOORTEN)], eigenaar, None, CLI)

    alle = leden.alle_leden()
    oud = [lid for lid in alle if leden.is_oud_lid(lid)]
    actief = [lid for lid in alle if not leden.is_oud_lid(lid)]
    clubboten = [boot(None) for _ in range(CLUBBOTEN)]
    oud_boten = [boot(lid.id, oud_lid=True) for lid in oud[:BOTEN_OUD_LID]]
    eigen = [boot(lid.id) for lid in r.choices(actief, k=BOTEN_LEDEN)]

    vrij = db.session.scalars(select(Plaats).order_by(Plaats.id)).all()
    geplaatst = 0
    for b in clubboten + oud_boten + eigen:
        if geplaatst == MET_PLAATS:
            break
        p = next((p for p in vrij if b.bootsoort in p.bootsoorten
                  and p.is_clubplaats == (b.lid_id is None)), None)
        if p is None:
            continue
        if b in oud_boten:
            # Een oud-lid met een plaats ontstaat in het echt door opzegging na toewijzen;
            # toewijzen zelf weigert een oud-lid.
            p.boot = b
            log.schrijf(CLI, "plaats.toegewezen", [f"plaats:{p.id}", f"rek:{p.rek_id}",
                                                   f"boot:{b.id}", f"lid:{b.lid_id}"],
                        {"plaats": p.code, "boot": b.naam, "seed": "oud-lid"})
            db.session.commit()
        else:
            try:
                toewijzing.toewijzen(p.id, b.id, CLI)
            except Regelfout:
                continue
        vrij.remove(p)
        geplaatst += 1
    echo(f"Seed klaar: {len(alle)} leden, {len(REKKEN)} rekken, "
         f"{len(REKKEN) * PLAATSEN_PER_REK} plaatsen, "
         f"{len(clubboten) + len(oud_boten) + len(eigen)} boten, {geplaatst} met een plaats.")
