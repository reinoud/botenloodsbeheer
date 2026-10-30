"""Worker-lus (ADR-007). Slice 1a: alleen de heartbeat; synchronisatie en opschoning volgen."""

import logging
import signal
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

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
            hartslag()
        except Exception:  # de lus draait door; de fout staat in de containerlog
            db.session.rollback()
            logger.exception("ronde mislukt")
        for _ in range(INTERVAL):
            if stoppen:
                break
            time.sleep(1)
    logger.info("worker gestopt")
