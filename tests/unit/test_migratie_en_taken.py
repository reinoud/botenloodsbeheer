"""Migratie omkeerbaar en gelijk aan de modellen; heartbeat van de worker; seed."""

from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from sqlalchemy import func, select, text
from sqlalchemy.exc import ProgrammingError

from app import seed, taken
from app.domein import leden
from app.models import Boot, Lid, Plaats, Rek, Taakrun, db
from tests.unit.conftest import nieuwe_database


def test_migratie_omkeerbaar_en_gelijk_aan_modellen(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "head")
    command.check(cfg)  # faalt als models.py en de migraties uit elkaar lopen
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


@pytest.mark.parametrize("sql", ["INSERT INTO lid (lidnummer, naam) VALUES ('9', 'X')",
                                 "UPDATE lid SET naam = 'X'", "DELETE FROM lid"])
def test_webgebruiker_leest_leden_alleen(app, sql):
    db.session.execute(select(Lid)).all()
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(sql))
    db.session.rollback()


def test_heartbeat(app):
    assert not taken.gezond()
    taken.hartslag()
    taken.hartslag()
    assert taken.gezond()
    assert len(db.session.scalars(select(Taakrun)).all()) == 1
    db.session.scalar(select(Taakrun)).beeindigd_op = datetime.now(UTC) - timedelta(minutes=3)
    db.session.commit()
    assert not taken.gezond()


@pytest.mark.worker  # seed draait in de worker (#9)
def test_seed_maakt_de_synthetische_loods(app):
    seed.seed(echo=lambda _: None)
    def tel(model, *waar):
        return db.session.scalar(select(func.count()).select_from(model).where(*waar))

    assert tel(Rek) == 10 and tel(Plaats) == 160 and tel(Plaats, Plaats.is_clubplaats) == 8
    assert tel(Lid) == 208 and tel(Boot) == 180 and tel(Boot, Boot.lid_id.is_(None)) == 6
    assert tel(Plaats, Plaats.boot_id.isnot(None)) == 150
    oud_met_plaats = [p for p in db.session.scalars(select(Plaats).where(Plaats.boot_id.isnot(None)))
                      if p.boot.lid and leden.is_oud_lid(p.boot.lid)]
    assert len(oud_met_plaats) == 4
    assert all(lid.email.endswith("@example.org") for lid in db.session.scalars(select(Lid)))
    seed.seed(echo=lambda _: None)  # tweede keer: niets
    assert tel(Rek) == 10


def test_seed_weigert_in_productie(app):
    app.config["APP_OMGEVING"] = "productie"
    with pytest.raises(seed.SeedFout):
        seed.seed()
