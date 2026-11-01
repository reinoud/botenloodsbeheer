"""Boten van leden en clubboten, met hooguit één foto (BLB-005, ADR-008)."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, afbeeldingen, leden, log
from app.domein.toewijzing import controleer_past
from app.models import Boot, Bootsoort, Lid, Plaats, db


def _verwijzingen(boot):
    return [f"boot:{boot.id}", *([f"lid:{boot.lid_id}"] if boot.lid_id else [])]


def boten():
    return db.session.scalars(
        select(Boot).order_by(Boot.naam, Boot.id).options(
            selectinload(Boot.lid), selectinload(Boot.plaats), selectinload(Boot.bootsoort)
        )
    ).all()


def zonder_plaats():
    return [b for b in boten() if b.plaats is None]


def boot(boot_id):
    b = db.session.get(Boot, boot_id)
    if b is None:
        raise Regelfout("Deze boot bestaat niet.")
    return b


def boot_aanmaken(naam, bootsoort_id, lid_id, foto, actor):
    """lid_id None maakt een clubboot: de vereniging is eigenaar."""
    naam = (naam or "").strip()
    if not 1 <= len(naam) <= 100:
        raise Regelfout("Geef de boot een naam van 1 tot 100 tekens.")
    soort = db.session.get(Bootsoort, bootsoort_id) if bootsoort_id else None
    if soort is None:
        raise Regelfout("Kies een bootsoort.")
    eigenaar = db.session.get(Lid, lid_id) if lid_id is not None else None
    if lid_id is not None and eigenaar is None:
        raise Regelfout("Dit lid bestaat niet.")
    if eigenaar is not None and leden.is_oud_lid(eigenaar):
        raise Regelfout(f"{eigenaar.naam} is oud-lid en krijgt geen nieuwe boot.")
    b = Boot(naam=naam, bootsoort=soort, lid_id=lid_id)
    if foto:
        b.afbeelding = afbeeldingen.verwerk(foto)
    db.session.add(b)
    db.session.flush()
    log.schrijf(actor, "boot.aangemaakt", _verwijzingen(b),
                {"naam": naam, "bootsoort": soort.naam, "clubboot": lid_id is None,
                 "foto": b.afbeelding is not None})
    db.session.commit()
    return b


def boot_wijzigen(boot_id, naam, bootsoort_id, lid_id, actor):
    """Wijzigt naam, bootsoort en eigenaar (lid_id None is een clubboot). Een boot met een plaats
    blijft passen bij die plaats. Het log krijgt alleen een regel bij een echt verschil.
    Vergrendeling: eerst de boot, dan de plaats van de boot; zo ziet de plaatsquery een
    toewijzing die vlak ervoor is gecommit (READ COMMITTED)."""
    naam = (naam or "").strip()
    try:
        if not 1 <= len(naam) <= 100:
            raise Regelfout("Geef de boot een naam van 1 tot 100 tekens.")
        soort = db.session.get(Bootsoort, bootsoort_id) if bootsoort_id else None
        if soort is None:
            raise Regelfout("Kies een bootsoort.")
        eigenaar = db.session.get(Lid, lid_id) if lid_id is not None else None
        if lid_id is not None and eigenaar is None:
            raise Regelfout("Dit lid bestaat niet.")
        b = db.session.get(Boot, boot_id, with_for_update=True, populate_existing=True)
        if b is None:
            raise Regelfout("Deze boot bestaat niet.")
        plaats = db.session.scalar(select(Plaats).where(Plaats.boot_id == b.id).with_for_update()
                                   .execution_options(populate_existing=True))
        if eigenaar is not None and lid_id != b.lid_id and leden.is_oud_lid(eigenaar):
            raise Regelfout(f"{eigenaar.naam} is oud-lid en krijgt geen nieuwe boot.")
        oud_lid_id, oude_soort, oude_naam = b.lid_id, b.bootsoort, b.naam
        if plaats is not None and (soort != oude_soort or (lid_id is None) != (oud_lid_id is None)):
            controleer_past(plaats, naam, soort, lid_id is not None)
    except Regelfout:
        db.session.rollback()
        raise
    gegevens = {}
    if naam != oude_naam:
        gegevens["naam"] = [oude_naam, naam]
    if soort != oude_soort:
        gegevens["bootsoort"] = [oude_soort.naam, soort.naam]
    if lid_id != oud_lid_id:
        # verwijzingen, geen namen: oud en nieuw zonder persoonsgegevens (BLB-005, ADR-006)
        gegevens["eigenaar"] = [f"lid:{i}" if i else "vereniging" for i in (oud_lid_id, lid_id)]
    if not gegevens:
        db.session.rollback()  # geen verschil: geen logregel, en het slot vrij
        return b
    b.naam, b.bootsoort, b.lid_id = naam, soort, lid_id
    leden_ids = dict.fromkeys(i for i in (oud_lid_id, lid_id) if i is not None)
    log.schrijf(actor, "boot.gewijzigd", [f"boot:{b.id}", *(f"lid:{i}" for i in leden_ids)], gegevens)
    db.session.commit()
    return b


def foto_vervangen(boot_id, inhoud, actor):
    """Pas na een geslaagde verwerking vervangt de nieuwe foto de oude (BLB-005)."""
    nieuw = afbeeldingen.verwerk(inhoud)
    b = db.session.get(Boot, boot_id, with_for_update=True)
    if b is None:
        raise Regelfout("Deze boot bestaat niet.")
    oud = b.afbeelding
    b.afbeelding = nieuw
    if oud:
        db.session.flush()  # eerst de verwijzing weg, dan de oude foto
        db.session.delete(oud)
    log.schrijf(actor, "boot.foto_vervangen" if oud else "boot.foto_toegevoegd", _verwijzingen(b))
    db.session.commit()


def boot_verwijderen(boot_id, actor):
    b = db.session.get(Boot, boot_id, with_for_update=True)
    if b is None:
        raise Regelfout("Deze boot bestaat niet.")
    if b.plaats is not None:
        db.session.rollback()
        raise Regelfout("Deze boot heeft een plaats. Geef de plaats eerst vrij.")
    foto = b.afbeelding
    log.schrijf(actor, "boot.verwijderd", _verwijzingen(b), {"naam": b.naam})
    db.session.delete(b)
    if foto:
        db.session.flush()
        db.session.delete(foto)
    db.session.commit()
