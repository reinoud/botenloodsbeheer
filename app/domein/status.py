"""Technische status (BLB-037, ADR-010): één functie voor /status en /status.json. Alleen lezen.
Er staan geen tokenwaarden, wachtwoorden of gegevens van leden in; een reden van een mislukte
import komt uit de vaste lijst van de applicatie (BLB-006)."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import select, text

from app.domein import boten, leden, opschonen
from app.models import Taakrun, Token, db
from app.taken import HEARTBEAT_MAX
from app.web.health import HEAD

IMPORT_MAX = timedelta(hours=26)
VERLOOPT_BINNEN = timedelta(days=31)  # "binnen een maand" (backlog vraag 1)
ERNST = ("ok", "waarschuwing", "fout")


def _laatste(taak, statussen=("geslaagd", "mislukt")):
    return db.session.scalar(
        select(Taakrun).where(Taakrun.taak == taak, Taakrun.status.in_(statussen))
        .order_by(Taakrun.beeindigd_op.desc().nulls_last(), Taakrun.id.desc()).limit(1))


def _run(run):
    if run is None:
        return {"tijdstip": None, "resultaat": None, "aantallen": {}, "reden": None}
    return {"tijdstip": run.beeindigd_op, "resultaat": run.status, "aantallen": run.aantallen,
            "reden": run.foutmelding}


def status():
    """Onderdelen met elk een status: ok, waarschuwing of fout. Tijdstippen als datetime."""
    nu = datetime.now(UTC)
    tz = ZoneInfo(current_app.config["TZ"])
    migratie = db.session.scalar(text("SELECT version_num FROM alembic_version"))

    hartslag = _laatste("heartbeat", ("geslaagd",))
    hartslag = hartslag and hartslag.beeindigd_op

    import_ = _laatste(leden.TAAK)
    geslaagd = _laatste(leden.TAAK, ("geslaagd",))
    import_oud = geslaagd is None or nu - geslaagd.beeindigd_op > IMPORT_MAX

    opschoning = _laatste(opschonen.TAAK)
    opgehaald = _laatste(boten.BOOTAANTALLEN, ("geslaagd",))

    actief = select(Token).where(Token.ingetrokken_op.is_(None), Token.verloopt_op > nu)
    robots = db.session.scalars(actief.where(Token.soort == "robot").order_by(Token.naam)).all()
    verlopend = db.session.scalars(
        actief.where(Token.verloopt_op <= nu + VERLOOPT_BINNEN).order_by(Token.verloopt_op)).all()

    onderdelen = {
        "database": {
            "status": "ok" if migratie == HEAD else "fout",
            "postgresql": db.session.scalar(text("SHOW server_version")),
            "migratie": migratie, "verwacht": HEAD},
        "worker": {
            "status": "ok" if hartslag and nu - hartslag < HEARTBEAT_MAX else "waarschuwing",
            "heartbeat": hartslag},
        "import": {
            "status": "waarschuwing" if import_oud or import_.status == "mislukt" else "ok",
            **_run(import_), "laatst_geslaagd": geslaagd and geslaagd.beeindigd_op},
        "opschoning": {
            "status": "waarschuwing" if opschoning and opschoning.status == "mislukt" else "ok",
            **_run(opschoning)},
        "api": {"status": "ok", "ingeschakeld": current_app.config["API_INGESCHAKELD"]},
        "robottokens": {
            "status": "ok",
            "tokens": [{"naam": t.naam, "laatste_aanroep": t.laatst_gebruikt_op}
                       for t in robots]},
        "bootaantallen": {"status": "ok", "laatst_opgehaald": opgehaald and opgehaald.beeindigd_op},
        "tokens_verlopen": {
            "status": "waarschuwing" if verlopend else "ok",
            "tokens": [{"naam": t.naam, "soort": t.soort,
                        "vervaldatum": t.verloopt_op.astimezone(tz).date()} for t in verlopend]},
    }
    totaal = max((o["status"] for o in onderdelen.values()), key=ERNST.index)
    return {"status": totaal, "versie": current_app.config["APP_VERSIE"], "tijdstip": nu,
            **onderdelen}
