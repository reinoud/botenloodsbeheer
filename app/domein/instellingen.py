"""Naam en logo van de vereniging (BLB-027, ADR-008, ADR-009). Staan in de tabel instelling; een
lege of ontbrekende naam is de neutrale standaard. Het logo is een afbeelding; de rij `logo` wijst
ernaar. De kleuren komen uit de Dajaks-basis (ADR-002)."""

from sqlalchemy import Text, cast, select
from sqlalchemy.dialects.postgresql import insert

from app.domein import Regelfout, afbeeldingen, log
from app.models import Afbeelding, Instelling, db

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


def logo():
    """Het kenmerk van het logo (de sleutel van de afbeelding), of None."""
    return db.session.scalar(
        select(Afbeelding.sleutel).join(Instelling, Instelling.waarde == cast(Afbeelding.id, Text))
        .where(Instelling.sleutel == "logo", Afbeelding.soort == "logo"))


def logo_op_kenmerk(kenmerk):
    """De afbeelding bij dit kenmerk, alleen als het een logo is (een foto heeft ook een sleutel)."""
    return db.session.scalar(select(Afbeelding).where(Afbeelding.sleutel == kenmerk,
                                                      Afbeelding.soort == "logo"))


def logo_vervangen(inhoud, actor):
    """Pas na een geslaagde verwerking vervangt het nieuwe logo het oude (ADR-008). De inhoud
    komt niet in het log, alleen de afmetingen."""
    nieuw = afbeeldingen.verwerk(inhoud, "logo", vorige=logo() is not None)
    rij = _vergrendel(["logo"])["logo"]
    oud = db.session.get(Afbeelding, int(rij.waarde)) if rij.waarde else None
    db.session.add(nieuw)
    db.session.flush()
    rij.waarde = str(nieuw.id)
    if oud:
        db.session.delete(oud)
    log.schrijf(actor, "instelling.logo_vervangen" if oud else "instelling.logo_toegevoegd",
                ["instelling:huisstijl"], {"breedte": nieuw.breedte, "hoogte": nieuw.hoogte})
    db.session.commit()
    return True


def logo_verwijderen(actor):
    rij = _vergrendel(["logo"])["logo"]
    oud = db.session.get(Afbeelding, int(rij.waarde)) if rij.waarde else None
    if oud is None:
        db.session.rollback()
        raise Regelfout("Er is geen logo om te verwijderen.")
    rij.waarde = ""
    db.session.delete(oud)
    log.schrijf(actor, "instelling.logo_verwijderd", ["instelling:huisstijl"])
    db.session.commit()
    return True
