"""Mutatielog: inhoud zonder geheimen, afscherming in de database en de indeling in twee logs
(ADR-006, BLB-024, BLB-043)."""

import ast
from pathlib import Path

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
    regels = log.regels(["beheerder:2"], technisch=True)
    assert [r.actie for r in regels] == ["beheerder.methode_ingesteld", "beheerder.uitgenodigd"]


def test_vergrendeling_staat_in_het_log(app):
    beheerder_met_wachtwoord()
    for _ in range(5):
        beheerders.wachtwoord_controleren("anna", "fout wachtwoord!")
    regel = log.regels(technisch=True)[0]
    assert regel.actie == "beheerder.vergrendeld"
    assert (regel.actor_soort, regel.actor_naam) == ("systeem", "systeem")  # #7


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


def gelogde_acties(map_="app"):
    """Elke handeling uit een aanroep van log.schrijf in de code, ook beide takken van een
    voorwaardelijke expressie. Een handeling die geen letterlijke tekst is, faalt."""
    acties = set()
    for pad in Path(map_).rglob("*.py"):
        for knoop in ast.walk(ast.parse(pad.read_text(encoding="utf-8"))):
            if (isinstance(knoop, ast.Call) and isinstance(knoop.func, ast.Attribute)
                    and knoop.func.attr == "schrijf" and getattr(knoop.func.value, "id", "") == "log"):
                teksten = [c.value for c in ast.walk(knoop.args[1]) if isinstance(c, ast.Constant)]
                assert teksten, f"{pad}:{knoop.lineno}: handeling is geen letterlijke tekst"
                acties.update(teksten)
    return acties


def test_elke_handeling_hoort_bij_precies_een_log():
    acties = gelogde_acties()
    assert {"boot.foto_toegevoegd", "boot.gewijzigd", "plaats.toegewezen", "api.geweigerd"} <= acties  # scan werkt
    assert "boot.gewijzigd" in log.BOOTMUTATIES
    assert not log.BOOTMUTATIES & log.TECHNISCH, "in beide logs"
    assert not acties - log.BOOTMUTATIES - log.TECHNISCH, "in geen enkel log"
    assert not (log.BOOTMUTATIES | log.TECHNISCH) - acties, "staat in een log maar wordt nergens geschreven"


def test_overzichten_tonen_alleen_bootmutaties(app):
    beheerders.uitnodigen("anna", CLI)
    log.schrijf(CLI, "plaats.toegewezen", ["beheerder:1"])
    db.session.commit()
    assert [r.actie for r in log.regels(["beheerder:1"])] == ["plaats.toegewezen"]
    assert [r.actie for r in log.regels(["beheerder:1"], technisch=True)] == [
        "beheerder.uitgenodigd"]


def test_technisch_log_toont_ook_oude_soorten(app):
    log.schrijf(CLI, "lid.aangemaakt", ["lid:1"])  # oude soort uit een eerdere versie
    db.session.commit()
    assert [r.actie for r in log.regels(technisch=True)] == ["lid.aangemaakt"]
    assert log.regels() == []
