"""Indeling van de loods: rekken, verdiepingen en vakken (BLB-001, BLB-002, BLB-003, BLB-044,
ADR-003), bootsoorten (BLB-028) en de openbare leesfunctie (BLB-020). Een plaats is een vak met de
aanduiding <rek>/<verdieping>/<vak>, zoals A/1/1."""

import io
import secrets

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, leden, log, vandaag
from app.models import (
    Boot,
    Bootsoort,
    Lid,
    Plaats,
    Rek,
    VerdiepingBootsoort,
    db,
    plaats_bootsoort,
)

# Zonder verwarrende tekens: geen 0, o, O, 1, l en I (ADR-003).
ALFABET = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
SLEUTELLENGTE = 10
VERDIEPINGEN = range(1, 6)
VAKKEN = range(1, 13)
NAAM_MAX = 10
OMSCHRIJVING_MAX = 60


def _naam(naam):
    naam = (naam or "").strip()
    if not 1 <= len(naam) <= NAAM_MAX or "/" in naam:
        raise Regelfout(f"Geef het rek een naam van 1 tot {NAAM_MAX} tekens, zonder /.")
    return naam


def _omschrijving(tekst):
    tekst = (tekst or "").strip()
    if len(tekst) > OMSCHRIJVING_MAX:
        raise Regelfout(f"De omschrijving heeft hooguit {OMSCHRIJVING_MAX} tekens.")
    return tekst


def _vakken(vakken):
    """De paren (verdieping, vak) die aan staan, zoals het raster ze toont."""
    paren = set(vakken)
    if not paren:
        raise Regelfout("Zet minstens één vak aan.")
    if any(v not in VERDIEPINGEN or k not in VAKKEN for v, k in paren):
        raise Regelfout(f"Een rek heeft verdieping {VERDIEPINGEN[0]} tot en met "
                        f"{VERDIEPINGEN[-1]} en vak {VAKKEN[0]} tot en met {VAKKEN[-1]}.")
    return paren


def _flush_rek(naam):
    try:
        db.session.flush()
    except IntegrityError as fout:
        db.session.rollback()
        # De index op lower(naam) vangt ook twee gelijktijdige aanvragen af.
        if fout.orig.diag.constraint_name == "uq_rek_naam":
            raise Regelfout(f"Er is al een rek met de naam {naam}.") from None
        raise


def _naam_vrij(naam, rek_id=None):
    q = select(Rek.naam).where(func.lower(Rek.naam) == naam.lower())
    if rek_id is not None:
        q = q.where(Rek.id != rek_id)
    bestaand = db.session.scalar(q)
    if bestaand is not None:
        raise Regelfout(f"Er is al een rek met de naam {bestaand}.")


def bootsoorten():
    return db.session.scalars(select(Bootsoort).order_by(Bootsoort.id)).all()


def _soortnaam(naam, bootsoort_id=None):
    """Getrimd, 1 tot 50 tekens, uniek zonder verschil in hoofdletters (BLB-028)."""
    naam = (naam or "").strip()
    if not 1 <= len(naam) <= 50:
        raise Regelfout("Geef de bootsoort een naam van 1 tot 50 tekens.")
    q = select(Bootsoort.naam).where(func.lower(Bootsoort.naam) == naam.lower())
    if bootsoort_id is not None:
        q = q.where(Bootsoort.id != bootsoort_id)
    bestaand = db.session.scalar(q)
    if bestaand is not None:
        raise Regelfout(f"De bootsoort {bestaand} bestaat al.")
    return naam


def _flush_soortnaam(naam):
    try:
        db.session.flush()
    except IntegrityError as fout:
        db.session.rollback()
        # shortcut: de index vergelijkt met hoofdletters; twee gelijktijdige namen die alleen
        # daarin verschillen komen er allebei door. Een index op lower(naam) vraagt een migratie.
        if fout.orig.diag.constraint_name == "bootsoort_naam_key":
            raise Regelfout(f"De bootsoort {naam} bestaat al.") from None
        raise


def bootsoort_toevoegen(naam, actor):
    naam = _soortnaam(naam)
    s = Bootsoort(naam=naam)
    db.session.add(s)
    _flush_soortnaam(naam)
    log.schrijf(actor, "bootsoort.toegevoegd", [f"bootsoort:{s.id}"], {"naam": naam})
    db.session.commit()
    return s


def _soort_vast(bootsoort_id):
    s = db.session.get(Bootsoort, bootsoort_id, with_for_update=True, populate_existing=True)
    if s is None:
        db.session.rollback()
        raise Regelfout("Deze bootsoort bestaat niet.")
    return s


def bootsoort_hernoemen(bootsoort_id, naam, actor):
    """Boten, plaatsen en wachtlijst verwijzen naar het id en tonen dus vanzelf de nieuwe naam.
    De rij is vergrendeld, zodat het log bij twee gelijktijdige wijzigingen de juiste oude naam
    krijgt."""
    s = _soort_vast(bootsoort_id)
    try:
        naam = _soortnaam(naam, s.id)
    except Regelfout:
        db.session.rollback()
        raise
    if naam != s.naam:
        log.schrijf(actor, "bootsoort.hernoemd", [f"bootsoort:{s.id}"], {"naam": [s.naam, naam]})
        s.naam = naam
        _flush_soortnaam(naam)
    db.session.commit()
    return s


def _aantal(n, enkel, meer):
    return f"{n} {enkel if n == 1 else meer}"


def bootsoort_verwijderen(bootsoort_id, actor):
    """Weigert als een boot of plaats de soort gebruikt. De rij is vergrendeld: wie een boot of
    plaats van deze soort maakt, neemt eerst een KEY SHARE-slot op de soort (boten, _soorten) en
    wacht dus, of ziet daarna dat de soort weg is."""
    s = _soort_vast(bootsoort_id)
    boten_ = db.session.scalar(select(func.count()).where(Boot.bootsoort_id == s.id))
    plaatsen = db.session.scalar(
        select(func.count()).select_from(plaats_bootsoort)
        .where(plaats_bootsoort.c.bootsoort_id == s.id))
    if boten_ or plaatsen:
        db.session.rollback()
        delen = [_aantal(n, *w) for n, w in ((boten_, ("boot", "boten")),
                                              (plaatsen, ("plaats", "plaatsen"))) if n]
        raise Regelfout(f"De bootsoort {s.naam} is in gebruik bij {' en '.join(delen)}. "
                        "Wijzig of verwijder die eerst.")
    log.schrijf(actor, "bootsoort.verwijderd", [f"bootsoort:{s.id}"], {"naam": s.naam})
    db.session.delete(s)
    db.session.commit()


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


# Bootsoort in de database naar de bestandsnaam in app/web/static/boten (issue #87, docker/
# maak_plaatjes.py). C11 gebruikt het plaatje van de Canadese kano; een soort die hier niet staat
# (bijvoorbeeld via BLB-028 toegevoegd) toont de naam als tekst.
PLAATJES = {"Kajak": "kajak", "Canadese kano": "canadese-kano", "C11": "canadese-kano",
            "Surfski": "surfski", "Wildwaterkano": "wildwaterboot"}


def plaatje(p):
    """Wat een vak van het rekoverzicht toont: bezet met het plaatje van de boot, anders vrij met
    het plaatje van de eerste bootsoort van de plaats. Een lege clubplaats is niet vrij voor
    leden: zelfde plaatje, met `club` voor de gestippelde rand. `alt` noemt alle soorten, `titel`
    is de tekstballon: bij een boot de bootnaam en de eigenaar."""
    soorten = [p.boot.bootsoort.naam] if p.boot else [s.naam for s in p.bootsoorten]
    basis = PLAATJES.get(soorten[0]) if soorten else None
    woord = "bezet" if p.boot else "leeg" if p.is_clubplaats else "vrij"
    if p.boot:
        stand = f"{p.boot.naam} ({p.boot.lid.naam if p.boot.lid else 'clubboot'})"
    else:
        stand = "clubplaats, leeg" if p.is_clubplaats else "vrij"
    return {
        "plaats_id": p.id,
        "bestand": f"{basis}-{'bezet' if p.boot else 'vrij'}.jpg" if basis else None,
        "tekst": soorten[0] if soorten and not basis else "",
        "club": p.is_clubplaats and not p.boot,
        "titel": f"{', '.join(soorten) or 'geen bootsoort'}: {stand}",
        "alt": ", ".join([f"Plaats {p.code}", ", ".join(soorten) or "geen bootsoort"]
                         + (["clubplaats"] if p.is_clubplaats else []) + [woord]),
    }


def rekoverzicht(rek):
    """De vakken van een rek als {(verdieping, vak): plaatje(p)}."""
    return {(p.verdieping, p.vak): plaatje(p) for p in rek.plaatsen}


def vrije_plaatsen(bootsoort_id=None):
    """Vrije plaatsen voor leden (BLB-015): zonder boot en geen clubplaats, in de volgorde van
    de loods. Met bootsoort_id alleen de plaatsen die voor die soort geschikt zijn."""
    q = (select(Plaats).join(Plaats.rek)
         .where(Plaats.boot_id.is_(None), Plaats.is_clubplaats.is_(False))
         .order_by(Rek.volgorde, Rek.id, Plaats.verdieping, Plaats.vak)
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
    return sorted(rijen, key=lambda r: (r[0], r[1].rek.volgorde, r[1].rek_id, r[1].verdieping,
                                        r[1].vak))


def plaatsen_van_opzeggende_leden():
    """Plaatsen met de boot van een lid met een opzegdatum in de toekomst (BLB-041), de vroegste
    opzegdatum eerst. Na die datum staat de plaats bij de plaatsen van oud-leden (BLB-018)."""
    return db.session.scalars(
        select(Plaats).join(Plaats.boot).join(Boot.lid).join(Plaats.rek)
        .where(Lid.opzegdatum > vandaag(), Lid.uit_bron_op.is_(None))
        .order_by(Lid.opzegdatum, Rek.volgorde, Rek.id, Plaats.verdieping, Plaats.vak)
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
    return [{"code": p.code, "omschrijving": r.omschrijving, "sleutel": p.publieke_sleutel,
             "club": p.is_clubplaats,
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


def _verdiepingsoorten(per_verdieping, vakken):
    """{verdieping: Bootsoort} voor de verdiepingen met een vak. Een keuze bij een verdieping
    zonder vak valt stil weg (BLB-001). Een onbekende of ongeldige id weigert alles. KEY SHARE,
    zoals _soorten: bootsoort_verwijderen wacht op ons in plaats van een FK-fout te geven."""
    keuze = {v: i for v, i in (per_verdieping or {}).items()
             if v in {v for v, _ in vakken} and i is not None}
    if not all(isinstance(i, int) and not isinstance(i, bool) for i in keuze.values()):
        raise Regelfout("Kies een bestaande bootsoort.")
    soorten = {s.id: s for s in db.session.scalars(
        select(Bootsoort).where(Bootsoort.id.in_(set(keuze.values())))
        .with_for_update(key_share=True))}
    if not set(keuze.values()) <= soorten.keys():
        raise Regelfout("Kies een bestaande bootsoort.")
    return {v: soorten[i] for v, i in keuze.items()}


def rek_aanmaken(naam, omschrijving, vakken, actor, bootsoort_per_verdieping=None):
    """Maakt het rek met een plaats per vak dat aan staat (BLB-001). bootsoort_per_verdieping is
    {verdieping: bootsoort-id}: elke plaats op die verdieping krijgt die soort, en het rek
    onthoudt haar voor vakken die later aan gaan (ADR-003 v2.2.0)."""
    naam, omschrijving, vakken = _naam(naam), _omschrijving(omschrijving), _vakken(vakken)
    try:
        soorten = _verdiepingsoorten(bootsoort_per_verdieping, vakken)
        _naam_vrij(naam)
    except Regelfout:
        db.session.rollback()
        raise
    volgorde = db.session.scalar(select(func.coalesce(func.max(Rek.volgorde), 0))) + 1
    r = Rek(naam=naam, omschrijving=omschrijving, volgorde=volgorde)
    db.session.add(r)
    _flush_rek(naam)
    log.schrijf(actor, "rek.aangemaakt", [f"rek:{r.id}"],
                {"naam": naam, "omschrijving": omschrijving, "vakken": len(vakken),
                 **({"bootsoorten": {str(v): s.naam for v, s in sorted(soorten.items())}}
                    if soorten else {})})
    db.session.add_all(VerdiepingBootsoort(rek_id=r.id, verdieping=v, bootsoort_id=s.id)
                       for v, s in soorten.items())
    _plaatsen_erbij(r, vakken, actor, soorten)
    db.session.commit()
    return r


def _plaatsen_erbij(r, vakken, actor, soorten):
    """Nieuwe plaatsen, geen clubplaats; soorten is {verdieping: Bootsoort}."""
    nieuw = [Plaats(rek=r, verdieping=v, vak=k, publieke_sleutel=_publieke_sleutel(),
                    bootsoorten=[soorten[v]] if v in soorten else [])
             for v, k in sorted(vakken)]
    db.session.add_all(nieuw)
    db.session.flush()
    for p in nieuw:
        # "plaatscode", want het log verbergt de waarde van een veld "code" (ADR-006).
        log.schrijf(actor, "plaats.aangemaakt", [f"plaats:{p.id}", f"rek:{r.id}"],
                    {"plaatscode": f"{r.naam}/{p.verdieping}/{p.vak}",
                     **({"bootsoorten": [s.naam for s in p.bootsoorten]} if p.bootsoorten else {})})


def rek_wijzigen(rek_id, naam, omschrijving, actor):
    """Naam en omschrijving. Een nieuwe naam verandert de aanduiding van alle plaatsen in het
    rek; publieke sleutels en toewijzingen blijven (ADR-003)."""
    r = rek(rek_id)
    naam, omschrijving = _naam(naam), _omschrijving(omschrijving)
    _naam_vrij(naam, r.id)
    wijzigingen = {k: [oud, nieuw] for k, oud, nieuw in (("naam", r.naam, naam),
                   ("omschrijving", r.omschrijving, omschrijving)) if oud != nieuw}
    if wijzigingen:
        log.schrijf(actor, "rek.gewijzigd", [f"rek:{r.id}"], wijzigingen)
        r.naam, r.omschrijving = naam, omschrijving
        _flush_rek(naam)
    db.session.commit()
    return r


def indeling_instellen(rek_id, vakken, actor):
    """Zet precies de vakken in vakken (paren van verdieping en vak) aan (BLB-044): ontbrekende
    plaatsen komen erbij, plaatsen die niet in vakken staan verdwijnen, en de rest blijft met
    boot, sleutel en instellingen. Weigert als een vak dat uit gaat een boot heeft. Het rek wordt
    eerst vergrendeld en daarna de plaatsen; toewijzen vergrendelt nooit het rek (geen deadlock)."""
    vakken = _vakken(vakken)
    try:
        r = db.session.get(Rek, rek_id, with_for_update=True, populate_existing=True)
        if r is None:
            raise Regelfout("Dit rek bestaat niet.")
        bestaand = {(p.verdieping, p.vak): p for p in db.session.scalars(
            select(Plaats).where(Plaats.rek_id == r.id).order_by(Plaats.verdieping, Plaats.vak)
            .with_for_update(of=Plaats).execution_options(populate_existing=True))}
        weg = [p for paar, p in bestaand.items() if paar not in vakken]
        bezet = next((p for p in weg if p.boot_id), None)
        if bezet:
            raise Regelfout(f"Op plaats {bezet.code} ligt een boot. Geef de plaats eerst vrij.")
        # KEY SHARE op de soort, zoals _soorten: bootsoort_verwijderen wacht dan op ons.
        soorten = {v: s for v, s in db.session.execute(
            select(VerdiepingBootsoort.verdieping, Bootsoort)
            .join(Bootsoort, Bootsoort.id == VerdiepingBootsoort.bootsoort_id)
            .where(VerdiepingBootsoort.rek_id == r.id)
            .with_for_update(key_share=True, of=Bootsoort))}
    except Regelfout:
        db.session.rollback()
        raise
    for p in weg:
        log.schrijf(actor, "plaats.verwijderd", [f"plaats:{p.id}", f"rek:{r.id}"],
                    {"plaatscode": p.code})
        db.session.delete(p)
    _plaatsen_erbij(r, vakken - bestaand.keys(), actor, soorten)
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


def _soorten(bootsoort_ids):
    # KEY SHARE: wacht op een lopende bootsoort_verwijderen in plaats van een fout van de FK.
    soorten = db.session.scalars(
        select(Bootsoort).where(Bootsoort.id.in_(bootsoort_ids)).order_by(Bootsoort.id)
        .with_for_update(key_share=True)).all()
    if not soorten:
        raise Regelfout("Kies minstens één bootsoort die op de plaats past.")
    return soorten


def plaats_wijzigen(plaats_id, bootsoort_ids, is_clubplaats, actor):
    """Geschikte bootsoorten en clubplaats (BLB-002, 003). De aanduiding wijzigt alleen met de
    naam van het rek. De plaats wordt eerst vergrendeld, zodat geen boot verschijnt tussen
    controle en wijziging."""
    try:
        p = db.session.get(Plaats, plaats_id, with_for_update=True)
        if p is None:
            raise Regelfout("Deze plaats bestaat niet.")
        soorten = _soorten(bootsoort_ids)
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
    if soorten != p.bootsoorten:
        wijzigingen["bootsoorten"] = [[s.naam for s in p.bootsoorten], [s.naam for s in soorten]]
        p.bootsoorten = soorten
    if is_clubplaats != p.is_clubplaats:
        wijzigingen["clubplaats"] = [p.is_clubplaats, is_clubplaats]
        p.is_clubplaats = is_clubplaats
    if wijzigingen:
        log.schrijf(actor, "plaats.gewijzigd", [f"plaats:{p.id}", f"rek:{p.rek_id}"], wijzigingen)
    db.session.commit()
    return p


def _publieke_sleutel():
    """Willekeurig en vast (ADR-003). Bij ongeveer 3 x 10^17 mogelijkheden is een botsing bij 160
    plaatsen verwaarloosbaar; de unieke constraint vangt die toch af."""
    return "".join(secrets.choice(ALFABET) for _ in range(SLEUTELLENGTE))


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
        "omschrijving": p.rek.omschrijving,
        "vrij": boot is None,
        "clubboot": boot is not None and boot.lid_id is None,
        "boot": boot.naam if boot else None,
        "foto": boot.afbeelding.sleutel if boot and boot.afbeelding else None,
        "eigenaar": boot.lid.naam if boot and boot.lid else None,
    }
