"""Worker-lus (ADR-007): heartbeat en ledensynchronisatie. De opschoning volgt in slice 6."""

import logging
import signal
import time
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import func, select

from app import ledenbron
from app.domein import LEDENSYNCHRONISATIE, Regelfout, leden, log
from app.models import Taakrun, db

INTERVAL = 15
HEARTBEAT_MAX = timedelta(minutes=2)
# Na een mislukte geplande synchronisatie hooguit één nieuwe poging per uur, zodat een
# storing van de bron geen logregel per ronde geeft.
NIEUWE_POGING = timedelta(hours=1)
SYNC_SLOT = 1  # sleutel van de advisory lock

logger = logging.getLogger(__name__)


def hartslag():
    nu = datetime.now(UTC)
    rij = db.session.scalar(select(Taakrun).where(Taakrun.taak == "heartbeat"))
    if rij is None:
        rij = Taakrun(taak="heartbeat", status="geslaagd", gestart_op=nu)
        db.session.add(rij)
    rij.beeindigd_op = nu
    db.session.commit()


def gezond():
    rij = db.session.scalar(select(Taakrun).where(Taakrun.taak == "heartbeat"))
    return rij is not None and datetime.now(UTC) - rij.beeindigd_op < HEARTBEAT_MAX


def _foutmelding(fout):
    # Alleen eigen meldingen gaan naar taakrun en log; een onverwachte fout kan een geheim
    # of persoonsgegeven bevatten en geeft alleen het soort fout.
    if isinstance(fout, (ledenbron.LedenbronFout, Regelfout)):
        return str(fout)
    return f"Onverwachte fout ({type(fout).__name__})."


def synchroniseer(run):
    """Draait de ledensynchronisatie voor een nieuwe of aangevraagde taakrun."""
    if not db.session.scalar(select(func.pg_try_advisory_xact_lock(SYNC_SLOT))):
        db.session.rollback()  # een andere worker is bezig
        return
    run_id = run.id
    db.session.add(run)
    run.status, run.gestart_op = "bezig", datetime.now(UTC)
    try:
        run.aantallen = leden.synchroniseer(ledenbron.kies(), LEDENSYNCHRONISATIE)
        run.status, run.beeindigd_op = "geslaagd", datetime.now(UTC)
        db.session.commit()
    except Exception as fout:  # noqa: BLE001  vastgelegd in taakrun en log, zonder inhoud
        db.session.rollback()
        logger.warning("ledensynchronisatie mislukt: %s", type(fout).__name__)
        run = db.session.get(Taakrun, run_id) if run_id else Taakrun(taak=leden.TAAK)
        db.session.add(run)
        run.status, run.beeindigd_op = "mislukt", datetime.now(UTC)
        run.gestart_op = run.gestart_op or run.beeindigd_op
        run.foutmelding = _foutmelding(fout)
        db.session.flush()
        log.schrijf(LEDENSYNCHRONISATIE, "leden.synchronisatie_mislukt", [f"taakrun:{run.id}"],
                    {"fout": run.foutmelding})
        db.session.commit()


def sync_gepland(nu=None):
    """Na SYNC_TIJDSTIP, als die vandaag nog niet slaagde en er het afgelopen uur geen poging was."""
    nu = (nu or datetime.now(UTC)).astimezone(ZoneInfo(current_app.config["TZ"]))
    if nu.time() < current_app.config["SYNC_TIJDSTIP"]:
        return False
    begin_dag = nu.replace(hour=0, minute=0, second=0, microsecond=0)
    runs = select(func.count()).select_from(Taakrun).where(Taakrun.taak == leden.TAAK)
    geslaagd = runs.where(Taakrun.status == "geslaagd", Taakrun.gestart_op >= begin_dag)
    recent = runs.where(Taakrun.gestart_op >= nu - NIEUWE_POGING)
    return not db.session.scalar(geslaagd) and not db.session.scalar(recent)


def ronde():
    hartslag()
    verzoek = db.session.scalar(
        select(Taakrun).where(Taakrun.taak == leden.TAAK, Taakrun.status == "aangevraagd")
        .order_by(Taakrun.id).limit(1)
    )
    if verzoek:
        synchroniseer(verzoek)
    elif sync_gepland():
        synchroniseer(Taakrun(taak=leden.TAAK, status="bezig"))


def draai():
    stoppen = False

    def stop(*_):
        nonlocal stoppen
        stoppen = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logger.info("worker gestart")
    while not stoppen:
        try:
            ronde()
        except Exception:  # de lus draait door; de fout staat in de containerlog
            db.session.rollback()
            logger.exception("ronde mislukt")
        for _ in range(INTERVAL):
            if stoppen:
                break
            time.sleep(1)
    logger.info("worker gestopt")
