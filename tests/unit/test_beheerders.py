"""Uitnodigen, wachtwoord met TOTP en vergrendeling (ADR-001, BLB-022)."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.domein import CLI, Regelfout, beheerders
from app.models import Beheerder, Uitnodiging, db
from tests.unit.hulp import WACHTWOORD, beheerder_met_wachtwoord, code_bij


def test_uitnodiging_bewaart_alleen_hash_en_is_24_uur_geldig(app):
    code = beheerders.uitnodigen("anna", CLI)
    u = db.session.scalar(select(Uitnodiging))
    assert code not in u.code_hash and len(u.code_hash) == 64
    assert timedelta(hours=23, minutes=59) < u.verloopt_op - datetime.now(UTC) <= timedelta(hours=24)
    assert beheerders.uitnodiging(code).beheerder.gebruikersnaam == "anna"


def test_verlopen_uitnodiging_geweigerd(app):
    code = beheerders.uitnodigen("anna", CLI)
    db.session.scalar(select(Uitnodiging)).verloopt_op = datetime.now(UTC) - timedelta(seconds=1)
    db.session.commit()
    with pytest.raises(Regelfout):
        beheerders.uitnodiging(code)


def test_uitnodiging_werkt_een_keer(app):
    _b, geheim = beheerder_met_wachtwoord()
    code = beheerders.uitnodigen("bert", CLI)
    beheerders.wachtwoord_instellen(code, WACHTWOORD, geheim, code_bij(geheim))
    with pytest.raises(Regelfout):
        beheerders.wachtwoord_instellen(code, WACHTWOORD, geheim, code_bij(geheim, 1))


@pytest.mark.parametrize("naam", ["a", "Anna", "anna jansen", "x" * 51])
def test_ongeldige_gebruikersnaam(app, naam):
    with pytest.raises(Regelfout):
        beheerders.uitnodigen(naam, CLI)


def test_gebruikersnaam_bestaat_al(app):
    beheerders.uitnodigen("anna", CLI)
    with pytest.raises(Regelfout):
        beheerders.uitnodigen("anna", CLI)


@pytest.mark.parametrize("wachtwoord", ["kort", "elf tekens!", "x" * 129])
def test_wachtwoordregels(app, wachtwoord):
    code = beheerders.uitnodigen("anna", CLI)
    geheim = beheerders.nieuw_totp_geheim()
    with pytest.raises(Regelfout):
        beheerders.wachtwoord_instellen(code, wachtwoord, geheim, code_bij(geheim))


def test_wachtwoord_gelijk_aan_gebruikersnaam_geweigerd(app):
    code = beheerders.uitnodigen("annajansen12", CLI)
    geheim = beheerders.nieuw_totp_geheim()
    with pytest.raises(Regelfout):
        beheerders.wachtwoord_instellen(code, "AnnaJansen12", geheim, code_bij(geheim))


def test_foute_totp_bij_instellen_verbruikt_uitnodiging_niet(app):
    code = beheerders.uitnodigen("anna", CLI)
    geheim = beheerders.nieuw_totp_geheim()
    with pytest.raises(Regelfout):
        beheerders.wachtwoord_instellen(code, WACHTWOORD, geheim, "000000"
                                        if code_bij(geheim) != "000000" else "111111")
    db.session.rollback()
    b = beheerders.wachtwoord_instellen(code, WACHTWOORD, geheim, code_bij(geheim))
    assert b.wachtwoordhash.startswith("$argon2id$")


def test_totp_geheim_versleuteld_opgeslagen(app):
    b, geheim = beheerder_met_wachtwoord()
    assert geheim.encode() not in b.totp_geheim


def test_inloggen_met_wachtwoord_en_totp(app):
    b, geheim = beheerder_met_wachtwoord()
    assert beheerders.wachtwoord_controleren("anna", WACHTWOORD) == b
    assert beheerders.totp_controleren(b.id, code_bij(geheim, 1)) == b


def test_totp_code_maar_een_keer_bruikbaar(app):
    b, geheim = beheerder_met_wachtwoord()
    # De huidige stap is bij het instellen gebruikt; die code werkt niet nog een keer.
    assert beheerders.totp_controleren(b.id, code_bij(geheim)) is None
    assert beheerders.totp_controleren(b.id, code_bij(geheim, 1)) == b
    assert beheerders.totp_controleren(b.id, code_bij(geheim, 1)) is None


def test_onbekende_gebruiker_en_fout_wachtwoord_geven_none(app):
    beheerder_met_wachtwoord()
    assert beheerders.wachtwoord_controleren("onbekend", WACHTWOORD) is None
    assert beheerders.wachtwoord_controleren("anna", "fout wachtwoord!") is None


def test_vergrendeling_na_vijf_fouten(app):
    b, geheim = beheerder_met_wachtwoord()
    for _ in range(4):
        assert beheerders.wachtwoord_controleren("anna", "fout wachtwoord!") is None
    assert beheerders.wachtwoord_controleren("anna", WACHTWOORD) == b  # nog niet vergrendeld
    beheerders.wachtwoord_controleren("anna", "fout wachtwoord!")
    b = db.session.get(Beheerder, b.id)
    assert b.geblokkeerd_tot > datetime.now(UTC) + timedelta(minutes=14)
    # Ook het juiste wachtwoord en een juiste code worden nu geweigerd.
    assert beheerders.wachtwoord_controleren("anna", WACHTWOORD) is None
    assert beheerders.totp_controleren(b.id, code_bij(geheim, 1)) is None
    # Na 15 minuten werkt het weer.
    b.geblokkeerd_tot = datetime.now(UTC) - timedelta(seconds=1)
    db.session.commit()
    assert beheerders.wachtwoord_controleren("anna", WACHTWOORD) == b


def test_foute_totp_codes_tellen_mee(app):
    b, _geheim = beheerder_met_wachtwoord()
    for _ in range(5):
        beheerders.totp_controleren(b.id, "000000")
    assert db.session.get(Beheerder, b.id).geblokkeerd_tot is not None


def test_juiste_totp_zet_teller_terug(app):
    b, geheim = beheerder_met_wachtwoord()
    for _ in range(4):
        beheerders.wachtwoord_controleren("anna", "fout wachtwoord!")
    beheerders.wachtwoord_controleren("anna", WACHTWOORD)
    beheerders.totp_controleren(b.id, code_bij(geheim, 1))
    assert db.session.get(Beheerder, b.id).mislukte_pogingen == 0


def test_inactief_account_kan_niet_inloggen(app):
    b, _geheim = beheerder_met_wachtwoord()
    b.actief = False
    db.session.commit()
    assert beheerders.wachtwoord_controleren("anna", WACHTWOORD) is None


def test_ongeldige_passkeygegevens_geweigerd(app):
    code = beheerders.uitnodigen("anna", CLI)
    with pytest.raises(Regelfout):
        beheerders.passkey_registreren(code, {"id": "x", "rawId": "x"}, b"challenge")
    assert beheerders.uitnodiging(code)  # niet verbruikt
    assert beheerders.passkey_inloggen({"rawId": "AAAA"}, b"challenge") is None
    assert beheerders.passkey_inloggen({}, b"challenge") is None
