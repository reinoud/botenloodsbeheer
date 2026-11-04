"""flask seed: een synthetische loods op de omvang van de vereniging (architectuur §6.3).

Vaste random seed, dus elke run levert hetzelfde op. Alle gegevens zijn verzonnen.
Afwijkingen van §6.3: de indeling komt uit de CSV-bestanden naast dit bestand (issue #80), seed
draait in de worker en importeert geen leden. De leden komen uit tests/fixtures/leden.json via de
integratiecontainer met de stub en PUT /api/v1/leden, de enige route die leden schrijft (ADR-012);
seed weigert zonder leden. Kleuren volgen met hun slice. Het testlogo komt niet uit seed maar uit
compose.dev.yml (ADR-008).
"""

import csv
import random
from datetime import timedelta
from pathlib import Path

from flask import current_app
from sqlalchemy import select

from app.domein import CLI, Regelfout, boten, indeling, leden, log, toewijzing, vandaag, wachtlijst
from app.models import Boot, Instelling, Lid, Plaats, Rek, db

VERENIGING = "Kanovereniging De Voorbeeldplas"
# De echte indeling (issue #80): rek met omschrijving, en per vak de bootsoort en clubplaats.
REKKEN_CSV = Path(__file__).with_name("seed_rekken.csv")
INDELING_CSV = Path(__file__).with_name("seed_indeling.csv")
# De verzonnen boten volgen de vakken: veel kajaks, weinig surfski en C11. Een clubboot past op
# rek A (kajak of Canadese kano). Wat geen plaats vindt, wacht of blijft zonder plaats.
SOORTEN = ("Kajak",) * 12 + ("Canadese kano",) * 3 + ("Wildwaterkano", "Surfski", "C11")
CLUBSOORTEN = ("Kajak", "Canadese kano")
NAMEN = ("Zeemeeuw", "Waterhoen", "Fuut", "Reiger", "IJsvogel", "Snoek", "Otter", "Bever",
         "Libel", "Golfje", "Stroom", "Kroos")
BOTEN_LEDEN = 170
BOTEN_OUD_LID = 4
CLUBBOTEN = 6
MET_PLAATS = 150
OP_WACHTLIJST = 10


class SeedFout(Exception):
    pass


def _csv(pad):
    with pad.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _indeling_opbouwen(soort):
    """11 rekken met 224 plaatsen uit de twee CSV-bestanden. Een bootsoort die nog niet bestaat
    (Wildwaterkano) komt erbij zoals BLB-028 dat doet."""
    vakken = _csv(INDELING_CSV)
    for naam in sorted({v["bootsoort"] for v in vakken} - soort.keys()):
        soort[naam] = indeling.bootsoort_toevoegen(naam, CLI).id
    for rij in _csv(REKKEN_CSV):
        eigen = [v for v in vakken if v["rek"] == rij["rek"]]
        rek = indeling.rek_aanmaken(
            rij["rek"], rij["omschrijving"], {(int(v["verdieping"]), int(v["vak"])) for v in eigen},
            CLI)
        for p in rek.plaatsen:
            v = next(v for v in eigen if (int(v["verdieping"]), int(v["vak"])) == (p.verdieping, p.vak))
            indeling.plaats_wijzigen(p.id, [soort[v["bootsoort"]]], v["clubplaats"] == "ja", CLI)


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
    _indeling_opbouwen(soort)

    def boot(eigenaar, oud_lid=False, soorten=SOORTEN):
        naam = f"{r.choice(NAMEN)} {r.randint(1, 99)}"
        if oud_lid:
            # De boot bestond al voor de opzegging; boot_aanmaken weigert een oud-lid.
            b = Boot(naam=naam, bootsoort_id=soort[r.choice(soorten)], lid_id=eigenaar)
            db.session.add(b)
            db.session.flush()
            log.schrijf(CLI, "boot.aangemaakt", [f"boot:{b.id}", f"lid:{eigenaar}"],
                        {"naam": naam, "bootsoort": b.bootsoort.naam, "clubboot": False,
                         "foto": False, "seed": "oud-lid"})  # #10: ook deze mutatie in het log
            db.session.commit()
            return b
        return boten.boot_aanmaken(naam, soort[r.choice(soorten)], eigenaar, None, CLI)

    alle = leden.alle_leden()
    oud = [lid for lid in alle if leden.is_oud_lid(lid)]
    actief = [lid for lid in alle if not leden.is_oud_lid(lid)]
    clubboten = [boot(None, soorten=CLUBSOORTEN) for _ in range(CLUBBOTEN)]
    oud_boten = [boot(lid.id, oud_lid=True) for lid in oud[:BOTEN_OUD_LID]]
    eigen = [boot(lid.id) for lid in r.choices(actief, k=BOTEN_LEDEN)]

    vrij = list(db.session.scalars(select(Plaats).order_by(Plaats.id)))
    aantal, geplaatst = len(vrij), 0
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
    # De eerste boten zonder plaats wachten, met een aanmelddatum tot drie jaar terug.
    wachtend = [b for b in eigen if b.plaats is None][:OP_WACHTLIJST]
    for b in wachtend:
        wachtlijst.erop_zetten(b.id, vandaag() - timedelta(days=r.randint(1, 3 * 365)), CLI)
    echo(f"Seed klaar: {len(alle)} leden, {len(indeling.rekken())} rekken, "
         f"{aantal} plaatsen, "
         f"{len(clubboten) + len(oud_boten) + len(eigen)} boten, {geplaatst} met een plaats, "
         f"{len(wachtend)} op de wachtlijst.")
