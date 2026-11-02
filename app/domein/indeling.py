"""Indeling van de loods: rekken en plaatsen (BLB-001 tot en met BLB-004, ADR-003), en de
openbare leesfunctie (BLB-020)."""

import io
import re
import secrets

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, leden, log, vandaag
from app.models import Boot, Bootsoort, Lid, Plaats, Rek, db

# Zonder verwarrende tekens: geen 0, o, O, 1, l en I (ADR-003).
ALFABET = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
SLEUTELLENGTE = 10
CODE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,19}")


def _naam(naam):
    naam = (naam or "").strip()
    if not 1 <= len(naam) <= 50:
        raise Regelfout("Geef het rek een naam van 1 tot 50 tekens.")
    return naam


def bootsoorten():
    return db.session.scalars(select(Bootsoort).order_by(Bootsoort.id)).all()


def rekken():
    return db.session.scalars(
        select(Rek).order_by(Rek.volgorde, Rek.id).options(
            selectinload(Rek.plaatsen).selectinload(Plaats.boot).selectinload(Boot.lid),
            selectinload(Rek.plaatsen).selectinload(Plaats.boot).selectinload(Boot.bootsoort),
            selectinload(Rek.plaatsen).selectinload(Plaats.bootsoorten),
        )
    ).all()


def status(p):
    """vrij, bezet of clubplaats (BLB-016); een clubplaats heet zo, ook met een clubboot erop."""
    return "clubplaats" if p.is_clubplaats else "bezet" if p.boot_id else "vrij"


def vrije_plaatsen(bootsoort_id=None):
    """Vrije plaatsen voor leden (BLB-015): zonder boot en geen clubplaats, in de volgorde van
    de loods. Met bootsoort_id alleen de plaatsen die voor die soort geschikt zijn."""
    q = (select(Plaats).join(Plaats.rek)
         .where(Plaats.boot_id.is_(None), Plaats.is_clubplaats.is_(False))
         .order_by(Rek.volgorde, Rek.id, Plaats.volgorde, Plaats.id)
         .options(selectinload(Plaats.rek), selectinload(Plaats.bootsoorten)))
    if bootsoort_id:
        q = q.where(Plaats.bootsoorten.any(Bootsoort.id == bootsoort_id))
    return db.session.scalars(q).all()


def plaatsen_van_oud_leden():
    """Plaatsen met de boot van een oud-lid (BLB-018), als (datum, plaats) met de oudste datum
    eerst. De datum is de opzegdatum, of de dag waarop het lid uit de bron verdween als dat
    eerder was."""
    dag = vandaag()
    plaatsen = db.session.scalars(
        select(Plaats).join(Plaats.boot).join(Boot.lid).options(
            selectinload(Plaats.rek), selectinload(Plaats.boot).selectinload(Boot.lid))
    ).all()
    rijen = [(min(d for d in (p.boot.lid.opzegdatum, p.boot.lid.uit_bron_op) if d and d <= dag), p)
             for p in plaatsen if leden.is_oud_lid(p.boot.lid, dag)]
    return sorted(rijen, key=lambda r: (r[0], r[1].code.lower()))


def plaatsen_van_opzeggende_leden():
    """Plaatsen met de boot van een lid met een opzegdatum in de toekomst (BLB-041), de vroegste
    opzegdatum eerst. Na die datum staat de plaats bij de plaatsen van oud-leden (BLB-018)."""
    return db.session.scalars(
        select(Plaats).join(Plaats.boot).join(Boot.lid)
        .where(Lid.opzegdatum > vandaag(), Lid.uit_bron_op.is_(None))
        .order_by(Lid.opzegdatum, func.lower(Plaats.code))
        .options(selectinload(Plaats.rek), selectinload(Plaats.boot).selectinload(Boot.lid))
    ).all()


# Besluit vraag 8: geen adres, telefoon, e-mail of foto. De kolommen kunnen later veranderen.
KOLOMMEN = ("Rek", "Code", "Status", "Bootsoort", "Bootnaam", "Eigenaar", "Lidnummer")


def geschikt_voor(p):
    """Kolom Bootsoort bij een plaats zonder boot, ook een clubplaats (besluit vraag 11)."""
    return f"(geschikt voor {', '.join(s.naam for s in p.bootsoorten)})"


def export(vereniging):
    """De indeling als .xlsx, een rij per plaats (BLB-017). Een clubboot heeft de vereniging
    als eigenaar en geen lidnummer."""
    boek = Workbook()
    blad = boek.active
    blad.title = "Indeling"
    blad.append(KOLOMMEN)
    for r in rekken():
        for p in r.plaatsen:
            b = p.boot
            soort = b.bootsoort.naam if b else geschikt_voor(p)
            rij = (r.naam, p.code, status(p), soort,
                   b.naam if b else None, (b.lid.naam if b.lid else vereniging) if b else None,
                   b.lid.lidnummer if b and b.lid else None)
            # Stuurtekens (mogelijk uit de ledenbron) weigert openpyxl; ze vallen weg.
            blad.append([ILLEGAL_CHARACTERS_RE.sub("", w) if w else w for w in rij])
    for rij in blad.iter_rows(min_row=2):
        for cel in rij:
            if cel.data_type == "f":  # tekst met = vooraan (zoals een naam uit de ledenbron)
                cel.data_type = "s"  # blijft tekst en wordt geen formule
    for cel, breedte in zip(blad[1], (12, 10, 12, 16, 24, 28, 12)):
        cel.font = Font(bold=True)
        blad.column_dimensions[cel.column_letter].width = breedte
    blad.freeze_panes = "A2"
    uit = io.BytesIO()
    boek.save(uit)
    return uit.getvalue()


def kaartjes(plaats_ids=(), rek_ids=(), alle=False):
    """Alleen wat op een kaartje mag (BLB-021, overlay §8), in de volgorde van de loods. Een
    clubplaats krijgt de naam van de vereniging (een clubboot ligt altijd op een clubplaats);
    eigenaar is None bij een vrije plaats."""
    return [{"code": p.code, "sleutel": p.publieke_sleutel, "club": p.is_clubplaats,
             "eigenaar": p.boot.lid.naam if p.boot and p.boot.lid else None}
            for r in rekken() for p in r.plaatsen
            if alle or r.id in rek_ids or p.id in plaats_ids]


def rek(rek_id):
    r = db.session.get(Rek, rek_id)
    if r is None:
        raise Regelfout("Dit rek bestaat niet.")
    return r


def plaats(plaats_id):
    p = db.session.get(Plaats, plaats_id)
    if p is None:
        raise Regelfout("Deze plaats bestaat niet.")
    return p


def rek_aanmaken(naam, actor):
    naam = _naam(naam)
    volgorde = db.session.scalar(select(func.coalesce(func.max(Rek.volgorde), 0))) + 1
    r = Rek(naam=naam, volgorde=volgorde)
    db.session.add(r)
    db.session.flush()
    log.schrijf(actor, "rek.aangemaakt", [f"rek:{r.id}"], {"naam": naam})
    db.session.commit()
    return r


def rek_wijzigen(rek_id, naam, actor):
    r = rek(rek_id)
    naam = _naam(naam)
    if naam != r.naam:
        log.schrijf(actor, "rek.gewijzigd", [f"rek:{r.id}"], {"naam": [r.naam, naam]})
        r.naam = naam
    db.session.commit()
    return r


def rek_verwijderen(rek_id, actor):
    """Verwijdert het rek met zijn lege plaatsen; weigert als er een boot op staat."""
    r = db.session.get(Rek, rek_id, with_for_update=True)
    if r is None:
        raise Regelfout("Dit rek bestaat niet.")
    plaatsen = db.session.scalars(
        select(Plaats).where(Plaats.rek_id == r.id).with_for_update()
    ).all()
    if any(p.boot_id for p in plaatsen):
        db.session.rollback()
        raise Regelfout("Op dit rek liggen nog boten. Geef eerst die plaatsen vrij.")
    for p in plaatsen:
        db.session.delete(p)
    log.schrijf(actor, "rek.verwijderd", [f"rek:{r.id}", *(f"plaats:{p.id}" for p in plaatsen)],
                {"naam": r.naam, "plaatsen": [p.code for p in plaatsen]})
    db.session.delete(r)
    db.session.commit()


def plaats_aanmaken(rek_id, code, bootsoort_ids, is_clubplaats, actor):
    r = rek(rek_id)
    code, soorten = _code(code), _soorten(bootsoort_ids)
    volgorde = len(r.plaatsen) + 1
    p = Plaats(rek=r, code=code, publieke_sleutel=_publieke_sleutel(),
               is_clubplaats=bool(is_clubplaats), volgorde=volgorde, bootsoorten=soorten)
    db.session.add(p)
    _flush_code(code)
    # "plaatscode", want het log verbergt de waarde van een veld "code" (ADR-006).
    log.schrijf(actor, "plaats.aangemaakt", [f"plaats:{p.id}", f"rek:{r.id}"],
                {"plaatscode": code, "bootsoorten": [s.naam for s in soorten],
                 "clubplaats": p.is_clubplaats})
    db.session.commit()
    return p


def _code(code):
    code = (code or "").strip()
    if not CODE.fullmatch(code):
        raise Regelfout("Een plaatscode heeft 1 tot 20 tekens: letters, cijfers, spatie, . _ of -.")
    return code


def _soorten(bootsoort_ids):
    soorten = db.session.scalars(
        select(Bootsoort).where(Bootsoort.id.in_(bootsoort_ids)).order_by(Bootsoort.id)).all()
    if not soorten:
        raise Regelfout("Kies minstens één bootsoort die op de plaats past.")
    return soorten


def _flush_code(code):
    try:
        db.session.flush()
    except IntegrityError as fout:
        db.session.rollback()
        # De database vergelijkt zonder hoofdletters, ook bij twee gelijktijdige aanvragen.
        if fout.orig.diag.constraint_name == "uq_plaats_code":
            raise Regelfout(f"De code {code} hoort al bij een andere plaats.") from None
        raise


def plaats_wijzigen(plaats_id, code, bootsoort_ids, is_clubplaats, actor):
    """Code, geschikte bootsoorten en clubplaats (BLB-002, 003, 004). De plaats wordt eerst
    vergrendeld, zodat geen boot verschijnt tussen controle en wijziging.
    De publieke sleutel blijft, dus de QR-link toont daarna de nieuwe code (ADR-003)."""
    try:
        p = db.session.get(Plaats, plaats_id, with_for_update=True)
        if p is None:
            raise Regelfout("Deze plaats bestaat niet.")
        code, soorten = _code(code), _soorten(bootsoort_ids)
        is_clubplaats = bool(is_clubplaats)
        b = p.boot
        if b is not None and b.bootsoort not in soorten:
            raise Regelfout(f"Op plaats {p.code} ligt {b.naam}, een {b.bootsoort.naam.lower()}. "
                            "Geef de plaats eerst vrij of laat die bootsoort staan.")
        if b is not None and is_clubplaats != p.is_clubplaats:
            raise Regelfout(f"Op plaats {p.code} ligt {b.naam}. Geef de plaats eerst vrij "
                            "voordat je de clubplaats wijzigt.")
    except Regelfout:
        db.session.rollback()
        raise
    wijzigingen = {}
    if code != p.code:
        wijzigingen["plaatscode"] = [p.code, code]
        p.code = code
    if soorten != p.bootsoorten:
        wijzigingen["bootsoorten"] = [[s.naam for s in p.bootsoorten], [s.naam for s in soorten]]
        p.bootsoorten = soorten
    if is_clubplaats != p.is_clubplaats:
        wijzigingen["clubplaats"] = [p.is_clubplaats, is_clubplaats]
        p.is_clubplaats = is_clubplaats
    if wijzigingen:
        _flush_code(code)
        log.schrijf(actor, "plaats.gewijzigd", [f"plaats:{p.id}", f"rek:{p.rek_id}"], wijzigingen)
    db.session.commit()
    return p


def _publieke_sleutel():
    """Willekeurig en vast (ADR-003). Bij ongeveer 3 x 10^17 mogelijkheden is een botsing bij 160
    plaatsen verwaarloosbaar; de unieke constraint vangt die toch af."""
    return "".join(secrets.choice(ALFABET) for _ in range(SLEUTELLENGTE))


def plaats_verwijderen(plaats_id, actor):
    p = db.session.get(Plaats, plaats_id, with_for_update=True)
    if p is None:
        raise Regelfout("Deze plaats bestaat niet.")
    if p.boot_id:
        db.session.rollback()
        raise Regelfout("Op deze plaats ligt een boot. Geef de plaats eerst vrij.")
    log.schrijf(actor, "plaats.verwijderd", [f"plaats:{p.id}", f"rek:{p.rek_id}"],
                {"plaatscode": p.code})
    db.session.delete(p)
    db.session.commit()


def openbaar(publieke_sleutel):
    """Alleen wat de openbare pagina mag tonen (ADR-003, overlay §5). Wat hier niet wordt
    opgehaald, kan ook niet in de pagina terechtkomen. None als de plaats niet bestaat.

    eigenaar is None bij een vrije plaats en bij een clubboot (dan de naam van de vereniging).
    """
    p = db.session.scalar(select(Plaats).where(Plaats.publieke_sleutel == publieke_sleutel))
    if p is None:
        return None
    boot = p.boot
    return {
        "code": p.code,
        "vrij": boot is None,
        "clubboot": boot is not None and boot.lid_id is None,
        "boot": boot.naam if boot else None,
        "foto": boot.afbeelding.sleutel if boot and boot.afbeelding else None,
        "eigenaar": boot.lid.naam if boot and boot.lid else None,
    }
