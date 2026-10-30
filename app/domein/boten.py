"""Boten van leden en clubboten, met hooguit één foto (BLB-005, ADR-008)."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, afbeeldingen, log
from app.models import Boot, Bootsoort, Lid, db


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
    if lid_id is not None and db.session.get(Lid, lid_id) is None:
        raise Regelfout("Dit lid bestaat niet.")
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
