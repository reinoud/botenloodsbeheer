"""Worker-lus (ADR-007): heartbeat en de dagelijkse opschoning na OPSCHOON_TIJDSTIP (BLB-026). De
import van leden doet de integratiecontainer via de API (ADR-012)."""

import logging
import signal
import time
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import select

from app.domein import opschonen
from app.models import Taakrun, db

INTERVAL = 15
HEARTBEAT_MAX = timedelta(minutes=2)

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


def ronde(nu=None):
    hartslag()
    nu = nu or datetime.now(ZoneInfo(current_app.config["TZ"]))
    if nu.time() >= current_app.config["OPSCHOON_TIJDSTIP"]:
        opschonen.draai(nu.date())


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
