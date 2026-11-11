"""Leden: de import via de API en de afgeleide oud-ledenstatus (ADR-004, ADR-012).

Leden worden niet in de applicatie aangemaakt of gewijzigd (BLB-006); alleen de import via
PUT /api/v1/leden schrijft. Records uit de bron zijn externe invoer en worden hier gevalideerd.
"""

import re
from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.domein import Regelfout, log, vandaag, wachtlijst
from app.models import Boot, Lid, Taakrun, db

TAAK = "ledenimport"
IMPORT_SLOT = 1  # sleutel van de advisory lock: nooit twee imports tegelijk
MAX_RECORDS = 5000
# Vaste lijst (BLB-006): de container kiest een reden, de tekst komt van de applicatie.
REDENEN = {
    "bron_onbereikbaar": "De ledenbron is niet bereikbaar.",
    "bron_onleesbaar": "Het antwoord van de ledenbron is onleesbaar.",
    "bron_geweigerd": "De ledenbron weigerde de inloggegevens.",
}
BEWAARJAREN = 5
LIDNUMMER = re.compile(r"[A-Za-z0-9-]{1,20}")
# Tekstvelden en hun maximumlengte; langer wordt ingekort.
TEKST = {"naam": 100}
DATUMS = ("lid_sinds", "opzegdatum")


class Ongeldig(ValueError):
    pass


class Veiligheidsgrens(Regelfout):
    pass


class ImportLoopt(Regelfout):
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


def bevat(kolom, zoek):
    """Voorwaarde: kolom bevat zoek, zonder onderscheid in hoofdletters of accenten (#232).
    Beide kanten gaan door unaccent van PostgreSQL (migratie 0021); % en _ in zoek zijn letterlijk.
    De escape komt na unaccent, want unaccent maakt van bijvoorbeeld ％ een % (AEG-01)."""
    patroon = func.unaccent(zoek)
    for teken in ("\\", "%", "_"):
        patroon = func.replace(patroon, teken, "\\" + teken)
    return func.unaccent(kolom).ilike(func.concat("%", patroon, "%"), escape="\\")


def alle_leden(zoek=""):
    """Alle leden, of die waarvan naam of lidnummer de zoektekst bevat (BLB-019)."""
    q = select(Lid).order_by(Lid.naam, Lid.lidnummer)
    if zoek := (zoek or "").strip():
        q = q.where(or_(bevat(Lid.naam, zoek), bevat(Lid.lidnummer, zoek)))
    return db.session.scalars(q).all()


def boot_of_lid_bevat(zoek):
    """Voorwaarde voor een query met Boot en Lid: de naam van de boot of van het lid bevat de
    zoektekst. Een lege zoektekst laat alles door."""
    if not (zoek := (zoek or "").strip()):
        return True
    return or_(bevat(Boot.naam, zoek), bevat(Lid.naam, zoek))


def lid(lid_id):
    gevonden = db.session.get(Lid, lid_id, options=[
        selectinload(Lid.boten).selectinload(Boot.plaats),
        selectinload(Lid.boten).selectinload(Boot.bootsoort),
        selectinload(Lid.boten).selectinload(Boot.wachtlijst)])
    if gevonden is None:
        raise Regelfout("Dit lid bestaat niet.")
    return gevonden


def _tekst(record, veld):
    waarde = record.get(veld)
    if waarde is None:
        return None
    # PostgreSQL weigert een NUL-teken in tekst: het record telt als ongeldig, geen 500 (#74).
    if not isinstance(waarde, str) or "\x00" in waarde:
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
    return velden


def synchroniseer(records, actor):
    """Verwerkt de volledige lijst uit de bron in de lopende transactie; de aanroeper commit.

    Gooit Veiligheidsgrens als minder dan de helft van de actieve leden terugkomt; er is dan
    nog niets gewijzigd. Wijzigingen in leden komen niet in het log (ADR-004 v2.1.0); de
    aantallen gaan naar taakrun. Boten van oud-leden gaan van de wachtlijst, met actor in het
    log (BLB-008, #27).
    """
    dag = vandaag()
    aantallen = {"ontvangen": len(records), "nieuw": 0, "bijgewerkt": 0, "uit_bron": 0,
                 "ongeldig": 0, "overgeslagen": 0}

    # Ook een record met een geldig lidnummer maar ongeldige velden telt als gezien: anders
    # zou een tikfout in een datum van een lid een oud-lid maken.
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
        raise Veiligheidsgrens(
            f"De import leverde {len(gezien)} leden, minder dan de helft van de {actief} "
            "actieve leden. Er is niets gewijzigd."
        )

    bestaand = {lid.lidnummer: lid for lid in db.session.scalars(select(Lid).with_for_update())}
    for nummer, velden in geldig.items():
        lid = bestaand.get(nummer)
        if lid is None:
            # Een oud-lid dat nog niet bestond, komt er niet in (ADR-004 stap 4, #203).
            if velden["opzegdatum"] and velden["opzegdatum"] <= dag:
                aantallen["overgeslagen"] += 1
                continue
            db.session.add(Lid(lidnummer=nummer, **velden))
            aantallen["nieuw"] += 1
            continue
        velden["uit_bron_op"] = None  # weer in de bron
        anders = [v for v, w in velden.items() if getattr(lid, v) != w]
        if anders:
            for v in anders:
                setattr(lid, v, velden[v])
            aantallen["bijgewerkt"] += 1

    for nummer, lid in bestaand.items():
        if nummer not in gezien and lid.uit_bron_op is None:
            lid.uit_bron_op = dag
            aantallen["uit_bron"] += 1
    wachtlijst.oud_leden_eraf(actor, dag)
    return aantallen


def _run_afsluiten(status, aantallen=None, foutmelding=None):
    """Legt de uitkomst vast in het oudste open verzoek, of in een nieuwe run (ADR-012)."""
    run = db.session.scalar(
        select(Taakrun).where(Taakrun.taak == TAAK, Taakrun.status == "aangevraagd")
        .order_by(Taakrun.id).limit(1).with_for_update()
    ) or Taakrun(taak=TAAK)
    db.session.add(run)
    nu = datetime.now(UTC)
    run.status, run.gestart_op, run.beeindigd_op = status, run.gestart_op or nu, nu
    run.aantallen, run.foutmelding = aantallen or {}, foutmelding


def importeer(records, actor):
    """PUT /api/v1/leden: de volledige lijst uit de bron (ADR-012), met het token als actor.
    Gooit Ongeldig (422), ImportLoopt (409) of Veiligheidsgrens (409); de laatste staat als
    mislukte run in taakrun. Geeft de aantallen."""
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise Ongeldig(f"leden moet een lijst zijn van hooguit {MAX_RECORDS} records.")
    if not db.session.scalar(select(func.pg_try_advisory_xact_lock(IMPORT_SLOT))):
        db.session.rollback()
        raise ImportLoopt("Er loopt al een import.")
    try:
        aantallen = synchroniseer(records, actor)
    except Veiligheidsgrens as fout:
        db.session.rollback()
        _run_afsluiten("mislukt", foutmelding=str(fout))
        db.session.commit()
        raise
    _run_afsluiten("geslaagd", aantallen)
    db.session.commit()
    return aantallen


def import_mislukt(reden):
    """POST /api/v1/leden/import-mislukt: alleen een reden uit de vaste lijst, zodat geen tekst
    van buiten in taakrun komt (BLB-006). Niet in het log (ADR-004 v2.1.0)."""
    if not isinstance(reden, str) or reden not in REDENEN:
        raise Ongeldig(f"reden moet een van {', '.join(REDENEN)} zijn.")
    _run_afsluiten("mislukt", foutmelding=REDENEN[reden])
    db.session.commit()


def import_aangevraagd():
    return db.session.scalar(
        select(Taakrun.id).where(Taakrun.taak == TAAK, Taakrun.status == "aangevraagd").limit(1)
    ) is not None


def import_aanvragen(actor):
    """Een verzoek voor de integratiecontainer (ADR-007). Een open verzoek wordt niet verdubbeld."""
    if import_aangevraagd():
        raise Regelfout("Er staat al een import klaar.")
    run = Taakrun(taak=TAAK, status="aangevraagd", aangevraagd_op=datetime.now(UTC))
    db.session.add(run)
    db.session.flush()
    log.schrijf(actor, "leden.import_aangevraagd", [f"taakrun:{run.id}"])
    db.session.commit()


def laatste_runs(limiet=5):
    return db.session.scalars(
        select(Taakrun).where(Taakrun.taak == TAAK).order_by(Taakrun.id.desc()).limit(limiet)
    ).all()
