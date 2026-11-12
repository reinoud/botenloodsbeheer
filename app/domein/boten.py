"""Boten van leden en clubboten, met hooguit één foto (BLB-005, ADR-008), en de bootaantallen per
lid (BLB-009)."""

from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, afbeeldingen, indeling, leden, log, wachtlijst
from app.domein.toewijzing import controleer_past
from app.models import Boot, Bootsoort, Lid, Plaats, Taakrun, db

BOOTAANTALLEN = "bootaantallen"  # taak in taakrun: wanneer de API ze voor het laatst leverde


def _verwijzingen(boot):
    return [f"boot:{boot.id}", *([f"lid:{boot.lid_id}"] if boot.lid_id else [])]


def boten(zoek="", bootsoort_id=None):
    """Alle boten, of die waarvan boot of eigenaar de zoektekst bevat en die van de bootsoort zijn."""
    q = select(Boot).outerjoin(Boot.lid).where(leden.boot_of_lid_bevat(zoek))
    if bootsoort_id:
        q = q.where(Boot.bootsoort_id == bootsoort_id)
    return db.session.scalars(
        q.order_by(Boot.naam, Boot.id).options(
            selectinload(Boot.lid), selectinload(Boot.plaats), selectinload(Boot.bootsoort),
            selectinload(Boot.wachtlijst)
        )
    ).all()


def zonder_plaats():
    return [b for b in boten() if b.plaats is None]


def zonder_eigenaar():
    """Boten met een onbekende eigenaar (geen lid, geen clubboot), op naam (#204)."""
    return db.session.scalars(
        select(Boot).where(Boot.lid_id.is_(None), Boot.clubboot.is_(False)).order_by(Boot.naam, Boot.id)
        .options(selectinload(Boot.plaats), selectinload(Boot.bootsoort))).all()


def aantal_zonder_eigenaar():
    """Voor het menu op elke pagina."""
    return db.session.scalar(select(func.count()).select_from(Boot).where(
        Boot.lid_id.is_(None), Boot.clubboot.is_(False)))


def boot(boot_id):
    b = db.session.get(Boot, boot_id)
    if b is None:
        raise Regelfout("Deze boot bestaat niet.")
    return b


def _soort(bootsoort_id):
    """KEY SHARE: wacht op een lopende bootsoort_verwijderen en geeft daarna None, in plaats van
    een fout van de FK bij het opslaan (BLB-028)."""
    if not bootsoort_id:
        return None
    return db.session.get(Bootsoort, bootsoort_id, with_for_update={"key_share": True},
                          populate_existing=True)


def _bootnaam(naam):
    """De naam van een boot; een stuurteken kan niet in een CSV-bestand (ADR-014 §1)."""
    naam = (naam or "").strip()
    if not 1 <= len(naam) <= 100 or indeling._stuurteken(naam):
        raise Regelfout("Geef de boot een naam van 1 tot 100 tekens, zonder stuurtekens.")
    return naam


def boot_aanmaken(naam, bootsoort_id, lid_id, foto, actor, clubboot=False):
    """Eigenaar is het lid van lid_id, of met clubboot de vereniging; zonder beide is de eigenaar
    onbekend (#204)."""
    b = _boot_aanmaken(naam, bootsoort_id, lid_id, foto, actor, clubboot)
    db.session.commit()
    return b


def _boot_aanmaken(naam, bootsoort_id, lid_id, foto, actor, clubboot=False):
    """Kern van boot_aanmaken zonder commit; de bezettingsimport (ADR-014 §3) doet er meer in
    één transactie."""
    naam = _bootnaam(naam)
    soort = _soort(bootsoort_id)
    if soort is None:
        raise Regelfout("Kies een bootsoort.")
    _controleer_eigenaar(lid_id, clubboot)
    eigenaar = db.session.get(Lid, lid_id) if lid_id is not None else None
    if lid_id is not None and eigenaar is None:
        raise Regelfout("Dit lid bestaat niet.")
    if eigenaar is not None and leden.is_oud_lid(eigenaar):
        raise Regelfout(f"{eigenaar.naam} is oud-lid en krijgt geen nieuwe boot.")
    b = Boot(naam=naam, bootsoort=soort, lid_id=lid_id, clubboot=clubboot)
    if foto:
        b.afbeelding = afbeeldingen.verwerk(foto)
    db.session.add(b)
    db.session.flush()
    log.schrijf(actor, "boot.aangemaakt", _verwijzingen(b),
                {"naam": naam, "bootsoort": soort.naam, "clubboot": clubboot,
                 "eigenaar_onbekend": lid_id is None and not clubboot,
                 "foto": b.afbeelding is not None})
    return b


def _controleer_eigenaar(lid_id, clubboot):
    if clubboot and lid_id is not None:
        raise Regelfout("Een clubboot heeft geen lid als eigenaar.")


def _eigenaar_tekst(lid_id, clubboot):
    """Voor het log: een verwijzing, geen naam (BLB-005, ADR-006)."""
    return f"lid:{lid_id}" if lid_id else "vereniging" if clubboot else "onbekend"


def boot_wijzigen(boot_id, naam, bootsoort_id, lid_id, actor, clubboot=False):
    """Wijzigt naam, bootsoort en eigenaar (lid_id, of clubboot; beide leeg is onbekend, ook bij een boot
    die al een eigenaar had, #233). Een boot met een plaats blijft passen bij die plaats; een clubboot
    op een clubplaats wordt dus pas onbekend nadat hij van die plaats af is. Het log krijgt alleen een regel bij een echt verschil. Een boot op de wachtlijst met een andere
    eigenaar gaat van de lijst (`wachtlijst.verwijderd`, reden `andere eigenaar`).
    Vergrendeling: eerst de boot, dan de plaats van de boot; zo ziet de plaatsquery een
    toewijzing die vlak ervoor is gecommit (READ COMMITTED)."""
    try:
        naam = _bootnaam(naam)
        soort = _soort(bootsoort_id)
        if soort is None:
            raise Regelfout("Kies een bootsoort.")
        _controleer_eigenaar(lid_id, clubboot)
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
        if clubboot and b.wachtlijst is not None:
            raise Regelfout(f"Boot {b.naam} staat op de wachtlijst. Een clubboot kan daar niet "
                            "op; haal de boot eerst van de wachtlijst.")
        oud_lid_id, oude_club, oude_soort, oude_naam = b.lid_id, b.clubboot, b.bootsoort, b.naam
        if plaats is not None and (soort != oude_soort or clubboot != oude_club):
            controleer_past(plaats, naam, soort, clubboot)
    except Regelfout:
        db.session.rollback()
        raise
    gegevens = {}
    if naam != oude_naam:
        gegevens["naam"] = [oude_naam, naam]
    if soort != oude_soort:
        gegevens["bootsoort"] = [oude_soort.naam, soort.naam]
    if (lid_id, clubboot) != (oud_lid_id, oude_club):
        gegevens["eigenaar"] = [_eigenaar_tekst(oud_lid_id, oude_club), _eigenaar_tekst(lid_id, clubboot)]
    if not gegevens:
        db.session.rollback()  # geen verschil: geen logregel, en het slot vrij
        return b
    # Besluit stakeholder 2026-11-01: een andere eigenaar haalt de boot van de wachtlijst. Een boot
    # waarvan de eigenaar onbekend was, houdt zijn plek: er verandert dan niemand (#204).
    if lid_id != oud_lid_id and oud_lid_id is not None and b.wachtlijst is not None:
        wachtlijst._eraf(b.wachtlijst, actor, "andere eigenaar")
    b.naam, b.bootsoort, b.lid_id, b.clubboot = naam, soort, lid_id, clubboot
    leden_ids = dict.fromkeys(i for i in (oud_lid_id, lid_id) if i is not None)
    log.schrijf(actor, "boot.gewijzigd", [f"boot:{b.id}", *(f"lid:{i}" for i in leden_ids)], gegevens)
    db.session.commit()
    return b


def eigenaar_kiezen(boot_id, lid_id, actor, clubboot=False):
    """Geeft een boot met een onbekende eigenaar een lid of de vereniging (pagina Boten zonder
    eigenaar, #204). Alleen zolang de eigenaar onbekend is: een andere beheerder kan hem intussen
    hebben gekozen. De rest van de regels (plaats, wachtlijst, oud-lid) is die van boot_wijzigen,
    in dezelfde transactie: het slot op de boot blijft staan."""
    b = db.session.get(Boot, boot_id, with_for_update=True, populate_existing=True)
    try:
        if b is None:
            raise Regelfout("Deze boot bestaat niet.")
        if b.lid_id is not None or b.clubboot:
            raise Regelfout(f"Boot {b.naam} heeft intussen een eigenaar. Er is niets gewijzigd.")
        if lid_id is None and not clubboot:
            raise Regelfout("Kies een eigenaar.")
        lid = db.session.get(Lid, lid_id) if lid_id is not None else None
        if lid is not None and leden.is_oud_lid(lid):
            raise Regelfout(f"Het gekozen lid van boot {b.naam} is intussen opgezegd. "
                            "Er is niets gewijzigd.")
    except Regelfout:
        db.session.rollback()
        raise
    return boot_wijzigen(boot_id, b.naam, b.bootsoort_id, lid_id, actor, clubboot)


def heeft_foto(boot_id):
    return db.session.scalar(select(Boot.afbeelding_id).where(Boot.id == boot_id)) is not None


def foto_vervangen(boot_id, inhoud, actor):
    """Pas na een geslaagde verwerking vervangt de nieuwe foto de oude (BLB-005)."""
    # heeft_foto alleen voor de melding; de vergrendeling volgt pas na de verwerking.
    nieuw = afbeeldingen.verwerk(inhoud, vorige=heeft_foto(boot_id))
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
    return True


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


def bootaantallen():
    """Per lid elke bootsoort met het aantal, ook 0 (ADR-004, ADR-012). Alleen boten met een
    plaats tellen; clubboten hebben geen lid en vallen dus weg (besluit 2026-10-31)."""
    soorten = db.session.scalars(select(Bootsoort.naam).order_by(Bootsoort.id)).all()
    telling = Counter(db.session.execute(
        select(Boot.lid_id, Bootsoort.naam).join(Boot.bootsoort).join(Boot.plaats)).all())
    leden = db.session.execute(select(Lid.id, Lid.lidnummer).order_by(Lid.lidnummer))
    return [{"lidnummer": nummer, "aantallen": {s: telling[(i, s)] for s in soorten}}
            for i, nummer in leden]


def bootaantallen_ophalen():
    """GET /api/v1/bootaantallen: legt het tijdstip vast voor de statuspagina (BLB-037)."""
    aantallen = bootaantallen()
    rij = db.session.scalar(select(Taakrun).where(Taakrun.taak == BOOTAANTALLEN)) or Taakrun(
        taak=BOOTAANTALLEN, status="geslaagd")
    db.session.add(rij)
    rij.gestart_op = rij.beeindigd_op = datetime.now(UTC)
    rij.aantallen = {"leden": len(aantallen)}
    db.session.commit()
    return aantallen
