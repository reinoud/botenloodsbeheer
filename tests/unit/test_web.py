"""Inloggen via de webinterface, sessies, CSRF, health en configuratie (BLB-022, ADR-001)."""

import time

import pytest
from cryptography.fernet import Fernet

from app import config, create_app
from app.domein import CLI, beheerders
from app.models import Beheerder, db
from tests.unit.hulp import WACHTWOORD, beheerder_met_wachtwoord, code_bij


def inloggen(client, geheim, stappen_verder=1, gebruikersnaam="anna"):
    client.post("/inloggen", data={"gebruikersnaam": gebruikersnaam, "wachtwoord": WACHTWOORD})
    return client.post("/inloggen/code", data={"code": code_bij(geheim, stappen_verder)})


def test_beheerpagina_vraagt_inloggen(client):
    for pad in ("/", "/log"):
        r = client.get(pad)
        assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_account_instellen_via_uitnodiging(app, client):
    code = beheerders.uitnodigen("anna", CLI)
    assert client.get(f"/uitnodiging/{code}").status_code == 200
    with client.session_transaction() as s:
        geheim = Fernet(app.config["TOTP_SLEUTEL"]).decrypt(s["totp_nieuw"].encode()).decode()
    r = client.post(f"/uitnodiging/{code}/wachtwoord", data={
        "wachtwoord": WACHTWOORD, "herhaling": WACHTWOORD, "code": code_bij(geheim)})
    assert r.status_code == 302 and r.location == "/"
    assert b"Welkom, anna" in client.get("/").data
    assert client.get(f"/uitnodiging/{code}").status_code == 404


def test_onbekende_uitnodiging(client):
    r = client.get("/uitnodiging/onzin")
    assert r.status_code == 404 and b"ongeldig" in r.data


def test_inloggen_en_uitloggen(app, client):
    _b, geheim = beheerder_met_wachtwoord()
    r = inloggen(client, geheim)
    assert r.location == "/"
    assert client.get("/log").status_code == 200
    with client.session_transaction() as s:
        oude_sessie = dict(s)
    client.post("/uitloggen")
    assert client.get("/").status_code == 302
    # Een bewaarde kopie van de oude sessie werkt niet meer: de sessieversie is opgehoogd.
    with client.session_transaction() as s:
        s.update(oude_sessie)
    assert client.get("/").status_code == 302


def test_fout_wachtwoord_en_foute_code_geven_dezelfde_melding(client):
    _b, _geheim = beheerder_met_wachtwoord()
    r1 = client.post("/inloggen", data={"gebruikersnaam": "anna", "wachtwoord": "fout!fout!fout"},
                     follow_redirects=True)
    client.post("/inloggen", data={"gebruikersnaam": "anna", "wachtwoord": WACHTWOORD})
    r2 = client.post("/inloggen/code", data={"code": "000000"}, follow_redirects=True)
    r3 = client.post("/inloggen", data={"gebruikersnaam": "niemand", "wachtwoord": WACHTWOORD},
                     follow_redirects=True)
    melding = b"Inloggen is mislukt."
    assert all(melding in r.data for r in (r1, r2, r3))


def test_codestap_zonder_wachtwoordstap(client):
    r = client.post("/inloggen/code", data={"code": "123456"})
    assert r.location.endswith("/inloggen")


def test_sessie_eindigt_bij_inactief_account(client):
    b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    db.session.get(Beheerder, b.id).actief = False
    db.session.commit()
    assert client.get("/").status_code == 302


def test_sessie_verloopt_na_12_uur(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    with client.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 12 * 3600 - 1
    assert client.get("/").status_code == 302


def test_csrf_verplicht(database):
    app = create_app({"TESTING": True})
    r = app.test_client().post("/inloggen", data={"gebruikersnaam": "a", "wachtwoord": "b"})
    assert r.status_code == 400


def test_health(client):
    assert client.get("/health/live").json == {"status": "ok"}
    assert client.get("/health/ready").json == {"status": "ok"}


def test_health_zonder_database(database):
    """BLB-036: live antwoordt zonder database, ready meldt niet gereed, zonder details."""
    app = create_app({"TESTING": True,
                      "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://x:y@db:1/geen",
                      "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"connect_timeout": 2}}})
    client = app.test_client()
    assert client.get("/health/live").json == {"status": "ok"}
    r = client.get("/health/ready")
    assert r.status_code == 503 and r.json == {"status": "niet gereed"}


def test_config_weigert_ontbrekende_of_onveilige_waarden(monkeypatch, tmp_path):
    monkeypatch.delenv("SECRET_KEY")
    with pytest.raises(config.ConfigFout, match="SECRET_KEY"):
        config.laad()
    geheim = tmp_path / "secret"
    geheim.write_text("y" * 40 + "\n")
    monkeypatch.setenv("SECRET_KEY_FILE", str(geheim))
    assert config.laad()["SECRET_KEY"] == "y" * 40
    monkeypatch.setenv("APP_OMGEVING", "productie")
    with pytest.raises(config.ConfigFout, match="https"):
        config.laad()
    monkeypatch.setenv("BASIS_URL", "https://loods.example.org")
    monkeypatch.setenv("TOTP_SLEUTEL", "geen-sleutel")
    with pytest.raises(config.ConfigFout, match="TOTP_SLEUTEL"):
        config.laad()


def test_totp_code_met_andere_tekens_geeft_gewone_melding(client):
    """#3: geen fout 500."""
    beheerder_met_wachtwoord()
    client.post("/inloggen", data={"gebruikersnaam": "anna", "wachtwoord": WACHTWOORD})
    r = client.post("/inloggen/code", data={"code": "１２３４５６"}, follow_redirects=True)
    assert r.status_code == 200 and b"Inloggen is mislukt." in r.data


def test_worker_heeft_geen_sessie_of_totp_sleutel_nodig(monkeypatch):
    """#7: de worker krijgt alleen de geheimen die hij gebruikt."""
    monkeypatch.setenv("DIENST", "worker")
    monkeypatch.delenv("SECRET_KEY")
    monkeypatch.delenv("TOTP_SLEUTEL")
    instellingen = config.laad()
    assert instellingen["SECRET_KEY"] is None and instellingen["TOTP_SLEUTEL"] is None
    monkeypatch.setenv("DIENST", "web")
    with pytest.raises(config.ConfigFout, match="TOTP_SLEUTEL"):
        config.laad()
