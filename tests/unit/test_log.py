"""Mutatielog: inhoud zonder geheimen en afscherming in de database (ADR-006, BLB-024)."""

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import ProgrammingError

from app.domein import CLI, beheerders, log
from app.models import Logregel, db
from tests.unit.conftest import TAKEN
from tests.unit.hulp import WACHTWOORD, beheerder_met_wachtwoord


def test_verboden_velden_komen_niet_in_het_log(app):
    log.schrijf(CLI, "test.actie", ["lid:1"], {"email": "a@example.org", "adres": "Straat 1",
                                               "wachtwoord": "geheim", "naam": "Boot"})
    db.session.commit()
    r = db.session.scalar(select(Logregel))
    assert r.gegevens == {"email": "gewijzigd", "adres": "gewijzigd", "wachtwoord": "gewijzigd",
                          "naam": "Boot"}


def test_uitnodigen_en_instellen_geven_logregels_zonder_geheimen(app):
    code = beheerders.uitnodigen("anna", CLI)
    b, geheim = beheerder_met_wachtwoord("bert")
    regels = db.session.scalars(select(Logregel).order_by(Logregel.id)).all()
    assert [r.actie for r in regels] == [
        "beheerder.uitgenodigd", "beheerder.uitgenodigd", "beheerder.methode_ingesteld"]
    assert regels[0].actor_naam == "cli" and regels[0].verwijzingen == ["beheerder:1"]
    tekst = str([(r.gegevens, r.verwijzingen, r.actor_naam) for r in regels])
    for geheim_deel in (code, geheim, WACHTWOORD, b.wachtwoordhash):
        assert geheim_deel not in tekst


def test_log_filtert_op_verwijzing_nieuwste_eerst(app):
    beheerders.uitnodigen("anna", CLI)
    beheerder_met_wachtwoord("bert")
    regels = log.regels("beheerder:2")
    assert [r.actie for r in regels] == ["beheerder.methode_ingesteld", "beheerder.uitgenodigd"]


def test_vergrendeling_staat_in_het_log(app):
    beheerder_met_wachtwoord()
    for _ in range(5):
        beheerders.wachtwoord_controleren("anna", "fout wachtwoord!")
    assert log.regels()[0].actie == "beheerder.vergrendeld"


@pytest.mark.parametrize("sql", ["UPDATE logregel SET actie = 'x'", "DELETE FROM logregel"])
def test_webgebruiker_kan_log_niet_wijzigen_of_verwijderen(app, sql):
    beheerders.uitnodigen("anna", CLI)
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(sql))
    db.session.rollback()


def test_taakgebruiker_mag_log_opschonen(app):
    beheerders.uitnodigen("anna", CLI)
    taken = create_engine(TAKEN)
    with taken.begin() as c:
        assert c.execute(text("DELETE FROM logregel")).rowcount == 1
        with pytest.raises(ProgrammingError, match="permission denied"):
            c.execute(text("UPDATE logregel SET actie = 'x'"))
    taken.dispose()
