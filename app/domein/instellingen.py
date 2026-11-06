"""Naam van de vereniging (BLB-027, ADR-009). Staat in de tabel instelling; een lege of
ontbrekende waarde is de neutrale standaard. De kleuren komen uit de Dajaks-basis (ADR-002) en
het logo uit de installatie (app.web.huisstijl.logo_laden, ADR-008)."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.domein import Regelfout, log
from app.models import Instelling, db

STANDAARD = {"naam": "Botenloods"}


def huidig():
    """De naam; een lege of ontbrekende waarde is de standaard."""
    waarden = {i.sleutel: i.waarde for i in db.session.scalars(select(Instelling))}
    return {k: waarden.get(k) or v for k, v in STANDAARD.items()}


def _vergrendel(sleutels):
    """Maakt ontbrekende rijen leeg aan en vergrendelt ze, zodat ook de eerste keer twee
    gelijktijdige wijzigingen op elkaar wachten."""
    db.session.execute(insert(Instelling).values([{"sleutel": s, "waarde": ""} for s in sleutels])
                       .on_conflict_do_nothing())
    rijen = db.session.scalars(select(Instelling).where(Instelling.sleutel.in_(sleutels))
                               .with_for_update().execution_options(populate_existing=True))
    return {i.sleutel: i for i in rijen}


def opslaan(naam, actor):
    """Slaat de naam op."""
    nieuw = {"naam": (naam or "").strip()}
    if not 1 <= len(nieuw["naam"]) <= 100:
        raise Regelfout("Geef de vereniging een naam van 1 tot 100 tekens.")
    rijen = _vergrendel(list(nieuw))
    wijzigingen = {}
    for k, waarde in nieuw.items():
        oud = rijen[k].waarde or STANDAARD[k]
        if waarde != oud:
            wijzigingen[k] = [oud, waarde]
        rijen[k].waarde = waarde
    if wijzigingen:
        log.schrijf(actor, "instelling.gewijzigd", ["instelling:huisstijl"], wijzigingen)
    db.session.commit()
