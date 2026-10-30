"""Migratie omkeerbaar en gelijk aan de modellen; heartbeat van de worker."""

from datetime import UTC, datetime, timedelta

from alembic import command
from sqlalchemy import select

from app import taken
from app.models import Taakrun, db
from tests.unit.conftest import nieuwe_database


def test_migratie_omkeerbaar_en_gelijk_aan_modellen(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "head")
    command.check(cfg)  # faalt als models.py en de migraties uit elkaar lopen
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


def test_heartbeat(app):
    assert not taken.gezond()
    taken.hartslag()
    taken.hartslag()
    assert taken.gezond()
    assert len(db.session.scalars(select(Taakrun)).all()) == 1
    db.session.scalar(select(Taakrun)).beeindigd_op = datetime.now(UTC) - timedelta(minutes=3)
    db.session.commit()
    assert not taken.gezond()
