"""Leden: synchronisatie met de ledenbron en de afgeleide oud-ledenstatus (ADR-004).

Leden worden niet in de applicatie aangemaakt of gewijzigd (BLB-006); alleen de synchronisatie
schrijft. Records uit de bron zijn externe invoer en worden hier gevalideerd.
"""

import re
from datetime import UTC, date, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, log, vandaag
from app.ledenbron import LedenbronFout
from app.models import Boot, Lid, Taakrun, db

TAAK = "ledensynchronisatie"
BEWAARJAREN = 5
LIDNUMMER = re.compile(r"[A-Za-z0-9-]{1,20}")
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
# Tekstvelden en hun maximumlengte; langer wordt ingekort.
TEKST = {"naam": 100, "adres": 200, "telefoon": 30, "email": 254}
DATUMS = ("lid_sinds", "opzegdatum")
VELDEN = (*TEKST, *DATUMS)


class Ongeldig(ValueError):
    pass


def jaren_terug(dag, jaren):
    try:
        return dag.replace(year=dag.year - jaren)
    except ValueError:  # 29 februari
        return dag.replace(year=dag.year - jaren, day=28)


def is_oud_lid(lid, dag=None):
    """Oud-lid: opzegdatum of uit_bron_op is gevuld en is niet later dan vandaag."""
    dag = dag or vandaag()
    return any(d is not None and d <= dag for d in (lid.opzegdatum, lid.uit_bron_op))


def actieve_leden():
    dag = vandaag()
    niet_opgezegd = or_(Lid.opzegdatum.is_(None), Lid.opzegdatum > dag)
    in_bron = or_(Lid.uit_bron_op.is_(None), Lid.uit_bron_op > dag)
    return db.session.scalars(
        select(Lid).where(niet_opgezegd, in_bron).order_by(Lid.naam, Lid.lidnummer)
    ).all()


def alle_leden(zoek=""):
    """Alle leden, of die waarvan naam of lidnummer de zoektekst bevat (BLB-019)."""
    q = select(Lid).order_by(Lid.naam, Lid.lidnummer)
    if zoek := (zoek or "").strip():
        q = q.where(or_(Lid.naam.icontains(zoek, autoescape=True),
                        Lid.lidnummer.icontains(zoek, autoescape=True)))
    return db.session.scalars(q).all()


def lid(lid_id):
    gevonden = db.session.get(Lid, lid_id, options=[
        selectinload(Lid.boten).selectinload(Boot.plaats),
        selectinload(Lid.boten).selectinload(Boot.bootsoort)])
    if gevonden is None:
        raise Regelfout("Dit lid bestaat niet.")
    return gevonden


def _tekst(record, veld):
    waarde = record.get(veld)
    if waarde is None:
        return None
    if not isinstance(waarde, str):
        raise Ongeldig(veld)
    return waarde.strip()[: TEKST[veld]] or None


def _datum(record, veld):
    waarde = record.get(veld)
    if waarde in (None, ""):
        return None
    if not isinstance(waarde, str):
        raise Ongeldig(veld)
    try:
        return date.fromisoformat(waarde)
    except ValueError:
        raise Ongeldig(veld) from None


def lidnummer_van(record):
    nummer = record.get("lidnummer") if isinstance(record, dict) else None
    if isinstance(nummer, int) and not isinstance(nummer, bool):
        nummer = str(nummer)
    if not isinstance(nummer, str) or not LIDNUMMER.fullmatch(nummer.strip()):
        return None
    return nummer.strip()


def valideer(record):
    """Geeft de velden van een geldig record, of gooit Ongeldig. Het lidnummer is al gecontroleerd."""
    velden = {v: _tekst(record, v) for v in TEKST} | {d: _datum(record, d) for d in DATUMS}
    if not velden["naam"]:
        raise Ongeldig("naam")
    if velden["email"] and not EMAIL.fullmatch(velden["email"]):
        raise Ongeldig("email")
    return velden


def synchroniseer(bron, actor):
    """Haalt alle leden op en verwerkt ze in de lopende transactie; de aanroeper commit.

    Gooit LedenbronFout als de bron faalt of als de veiligheidsgrens wordt geraakt; er is dan
    nog niets gewijzigd. Geeft de aantallen terug.
    """
    records = bron.haal_leden()
    dag = vandaag()
    grens = jaren_terug(dag, BEWAARJAREN)
    aantallen = {"ontvangen": len(records), "nieuw": 0, "bijgewerkt": 0, "uit_bron": 0,
                 "ongeldig": 0, "overgeslagen": 0}

    # Ook een record met een geldig lidnummer maar ongeldige velden telt als gezien: anders
    # zou een tikfout in een e-mailadres van een lid een oud-lid maken.
    gezien, geldig = set(), {}
    for record in records:
        nummer = lidnummer_van(record)
        if nummer is None or nummer in gezien:
            aantallen["ongeldig"] += 1
            continue
        gezien.add(nummer)
        try:
            geldig[nummer] = valideer(record)
        except Ongeldig:
            aantallen["ongeldig"] += 1  # zonder de inhoud te loggen

    actief = len(actieve_leden())
    if actief and len(gezien) * 2 < actief:
        raise LedenbronFout(
            f"De bron leverde {len(gezien)} leden, minder dan de helft van de {actief} actieve "
            "leden. Er is niets gewijzigd."
        )

    bestaand = {lid.lidnummer: lid for lid in db.session.scalars(select(Lid).with_for_update())}
    gewijzigd = []
    for nummer, velden in geldig.items():
        lid = bestaand.get(nummer)
        if lid is None:
            # Een opgeschoond oud-lid komt niet terug (ADR-004 stap 4).
            if velden["opzegdatum"] and velden["opzegdatum"] < grens:
                aantallen["overgeslagen"] += 1
                continue
            lid = Lid(lidnummer=nummer, **velden)
            db.session.add(lid)
            gewijzigd.append((lid, "lid.aangemaakt", list(VELDEN)))
            aantallen["nieuw"] += 1
            continue
        velden["uit_bron_op"] = None  # weer in de bron
        anders = [v for v, w in velden.items() if getattr(lid, v) != w]
        if anders:
            for v in anders:
                setattr(lid, v, velden[v])
            gewijzigd.append((lid, "lid.bijgewerkt", anders))
            aantallen["bijgewerkt"] += 1

    for nummer, lid in bestaand.items():
        if nummer not in gezien and lid.uit_bron_op is None:
            lid.uit_bron_op = dag
            gewijzigd.append((lid, "lid.uit_bron", ["uit_bron_op"]))
            aantallen["uit_bron"] += 1

    db.session.flush()
    for lid, actie, velden in gewijzigd:
        # Alleen de namen van de velden; geen waarden en geen naam van het lid (ADR-006).
        log.schrijf(actor, actie, [f"lid:{lid.id}"], {"velden": velden})
    log.schrijf(actor, "leden.gesynchroniseerd", [], aantallen)
    return aantallen


def synchronisatie_aanvragen(actor):
    """Een verzoek voor de worker (ADR-007). Een open verzoek wordt niet verdubbeld."""
    open_verzoek = db.session.scalar(
        select(Taakrun).where(Taakrun.taak == TAAK, Taakrun.status.in_(("aangevraagd", "bezig")))
    )
    if open_verzoek:
        raise Regelfout("Er loopt al een synchronisatie of er staat er een klaar.")
    run = Taakrun(taak=TAAK, status="aangevraagd", aangevraagd_op=datetime.now(UTC))
    db.session.add(run)
    db.session.flush()
    log.schrijf(actor, "leden.synchronisatie_aangevraagd", [f"taakrun:{run.id}"])
    db.session.commit()


def laatste_runs(limiet=5):
    return db.session.scalars(
        select(Taakrun).where(Taakrun.taak == TAAK).order_by(Taakrun.id.desc()).limit(limiet)
    ).all()
