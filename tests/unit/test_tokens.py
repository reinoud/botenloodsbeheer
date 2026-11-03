"""Slice 5: robottoken via de CLI, controle per aanroep, log en contract van de API (ADR-005,
ADR-012; BLB-029, 031, 032, 033, 034)."""

import hashlib
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

import jsonschema
import pytest
import yaml
from openapi_spec_validator import validate
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import ProgrammingError

from app.config import ConfigFout
from app.domein import CLI, Regelfout, tokens
from app.models import Logregel, Token, db
from tests.unit.conftest import API, EIGENAAR, WEB
from tests.unit.hulp import als_web

KOPPEL = {"X-Forwarded-For": "10.203.0.5"}
IMPORT = ["leden:importeren"]
SPEC = yaml.safe_load((Path(__file__).parents[2] / "app/api/openapi.yaml").read_text())


def maak(naam="integratie", rechten=IMPORT, whitelist=(), dagen=None):
    return tokens.robot_maken(naam, rechten, list(whitelist), dagen, CLI)


def maak_als_web(**kw):
    """Maakt een token zoals de CLI in web dat doet; voor tests die als de dienst api draaien."""
    return als_web(lambda: maak(**kw))


def eigenaar(sql, **params):
    engine = create_engine(EIGENAAR)
    with engine.begin() as c:
        c.execute(text(sql), params)
    engine.dispose()


def bearer(waarde):
    return {"Authorization": f"Bearer {waarde}"}


def logregels(actie):
    return db.session.scalars(select(Logregel).where(Logregel.actie == actie)
                              .order_by(Logregel.id)).all()


# Maken en intrekken (domein, als web)


def test_token_heeft_de_vorm_uit_adr_005_en_alleen_de_hash_staat_in_de_database(app):
    waarde = maak()
    assert tokens.TOKEN.fullmatch(waarde) and len(waarde) == 64
    t = db.session.scalar(select(Token))
    assert t.prefix == waarde[4:12] and t.soort == "robot"
    assert t.hash == hashlib.sha256(waarde.encode()).hexdigest()
    assert waarde[12:] not in str([t.prefix, t.hash, t.naam])


def test_robot_zonder_whitelist_en_dagen_krijgt_koppelnet_en_365_dagen(app):
    """BLB-031 criteria 1 en 2: logregel met actor cli zonder tokenwaarde."""
    waarde = maak()
    t = db.session.scalar(select(Token))
    assert [str(n) for n in t.ip_whitelist] == ["10.203.0.0/24"]
    assert abs(t.verloopt_op - datetime.now(UTC) - timedelta(days=365)) < timedelta(minutes=1)
    [regel] = logregels("token.gemaakt")
    assert (regel.actor_soort, regel.actor_naam, regel.verwijzingen) == ("systeem", "cli",
                                                                         [f"token:{t.id}"])
    assert regel.gegevens["whitelist"] == ["10.203.0.0/24"]
    assert waarde not in str(regel.gegevens) and waarde[12:] not in str(regel.gegevens)


def test_geldigheid_hooguit_3_jaar(app):
    """BLB-031 criterium 3. 1095 dagen (3 x 365) mag, één dag meer niet."""
    maak("drie-jaar", dagen=3 * 365)
    with pytest.raises(Regelfout, match="1095 dagen"):
        maak("een-dag-te-lang", dagen=3 * 365 + 1)
    with pytest.raises(Regelfout):
        maak("nul", dagen=0)
    assert db.session.scalars(select(Token.naam)).all() == ["drie-jaar"]


@pytest.mark.parametrize("rechten,melding", [([], "minstens één recht"),
                                             (["leden:schrijven"], "Onbekend recht")])
def test_zonder_of_met_onbekend_recht_geweigerd(app, rechten, melding):
    """BLB-032 criterium 1."""
    with pytest.raises(Regelfout, match=melding):
        maak(rechten=rechten)
    assert db.session.scalar(select(Token)) is None


@pytest.mark.parametrize("reeks", ["10.203.0.1/24", "geen-adres", "10.0.0.0/33", "fd00::1/129",
                                   "", "10.203.0.0/24, 10.0.0.0/8"])
def test_ongeldige_whitelist_geweigerd(app, reeks):
    """BLB-033 criterium 3."""
    with pytest.raises(Regelfout, match="Whitelist"):
        maak(whitelist=[reeks])


def test_whitelist_met_ipv4_en_ipv6(app):
    maak(whitelist=["10.203.0.7", "fd00::/64"])
    netten = db.session.scalar(select(Token.ip_whitelist))
    assert [str(n) for n in netten] == ["10.203.0.7/32", "fd00::/64"]


def test_naam_is_uniek(app):
    maak()
    with pytest.raises(Regelfout, match="al een token"):
        maak(rechten=["bootaantallen:lezen"])


def test_intrekken_met_logregel(app):
    maak()
    tokens.intrekken("integratie", CLI)
    assert db.session.scalar(select(Token.ingetrokken_op)) is not None
    [regel] = logregels("token.ingetrokken")
    assert regel.actor_naam == "cli" and regel.gegevens == {"naam": "integratie"}
    with pytest.raises(Regelfout, match="geen actief token"):
        tokens.intrekken("integratie", CLI)


# Controle per aanroep (domein)


def test_zonder_recht_403(app):
    """De volgorde van ADR-005 eindigt met het recht; /ik vraagt geen recht, dus hier direct."""
    waarde = maak(rechten=["bootaantallen:lezen"])
    with pytest.raises(tokens.Geweigerd) as w:
        tokens.controleer(f"Bearer {waarde}", "10.203.0.5", "leden:importeren", "/api/v1/x")
    assert (w.value.reden, w.value.status) == ("zonder_recht", 403)
    assert tokens.controleer(f"Bearer {waarde}", "10.203.0.5", "bootaantallen:lezen", "/x")


# De API zelf, als de dienst api met de rol botenloods_api


@pytest.mark.api
def test_ik_geeft_naam_rechten_en_vervaldatum_zonder_logregel(client):
    """BLB-029 criterium 1, BLB-031 criterium 2, BLB-034 criterium 5: een geslaagde aanroep
    werkt alleen laatst_gebruikt_op bij en komt niet in het log (ADR-005 v1.2.0)."""
    waarde = maak_als_web(rechten=["leden:importeren", "bootaantallen:lezen"])
    r = client.get("/api/v1/ik", headers=bearer(waarde) | KOPPEL)
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    verwacht = (datetime.now(UTC) + timedelta(days=365)).date().isoformat()
    assert r.json["token"] == "integratie"
    assert r.json["rechten"] == ["leden:importeren", "bootaantallen:lezen"]
    assert r.json["verloopt_op"] in (verwacht, (datetime.now(UTC) + timedelta(days=366))
                                     .date().isoformat())  # TZ kan over middernacht gaan
    jsonschema.validate(r.json, SPEC["components"]["schemas"]["Ik"])
    assert db.session.scalar(select(Token.laatst_gebruikt_op)) is not None
    assert [x.actie for x in db.session.scalars(select(Logregel))] == ["token.gemaakt"]


@pytest.mark.api
@pytest.mark.parametrize("ip,status", [("fd00::5", 200), ("fd01::5", 401), ("10.203.0.5", 401)])
def test_whitelist_ipv6(client, ip, status):
    """BLB-033 criteria 1 en 2, voor IPv6."""
    waarde = maak_als_web(whitelist=["fd00::/64"])
    r = client.get("/api/v1/ik", headers=bearer(waarde) | {"X-Forwarded-For": ip})
    assert r.status_code == status


@pytest.mark.api
@pytest.mark.parametrize("geval,reden", [
    ("zonder", "onbekend"), ("ander_schema", "onbekend"), ("onzin", "onbekend"),
    ("prefix_klopt_geheim_niet", "onbekend"), ("ingetrokken", "ingetrokken"),
    ("verlopen", "verlopen"), ("buiten_whitelist", "buiten_whitelist")])
def test_weigeringen_geven_hetzelfde_antwoord_en_een_logregel(client, geval, reden):
    """BLB-034 criterium 1, BLB-033 criterium 2, ADR-012 v1.1.0 (intrekken). De reden staat
    alleen in het log."""
    waarde = maak_als_web()
    ip = "10.203.0.5"
    headers = {
        "zonder": {},
        "ander_schema": {"Authorization": f"Basic {waarde}"},
        "onzin": bearer("blb_onzin"),
        "prefix_klopt_geheim_niet": bearer(waarde[:12] + "A" * 52),
    }.get(geval, bearer(waarde))
    if geval == "ingetrokken":
        eigenaar("UPDATE token SET ingetrokken_op = now()")
    if geval == "verlopen":
        eigenaar("UPDATE token SET verloopt_op = now() - interval '1 second'")
    if geval == "buiten_whitelist":
        ip = "10.204.0.5"
    r = client.get("/api/v1/ik", headers=headers | {"X-Forwarded-For": ip})
    assert (r.status_code, r.json) == (401, {"fout": "Geen toegang."})
    [regel] = logregels("api.geweigerd")
    assert regel.soort == "api" and regel.gegevens == {"endpoint": "/api/v1/ik", "reden": reden,
                                                       "ip": ip}
    assert regel.actor_naam == ("onbekend" if reden == "onbekend" else "integratie")
    assert waarde[12:] not in str([regel.gegevens, regel.verwijzingen, regel.actor_naam])


@pytest.mark.api
def test_token_werkt_tot_het_verloopt(client):
    """Tegenhanger van het geval verlopen hierboven: een minuut ervoor werkt het nog."""
    waarde = maak_als_web()
    eigenaar("UPDATE token SET verloopt_op = now() + interval '1 minute'")
    assert client.get("/api/v1/ik", headers=bearer(waarde) | KOPPEL).status_code == 200


@pytest.mark.api
def test_api_uit_weigert_elke_aanroep(client):
    """BLB-029 criterium 2. Dezelfde aanroep slaagt met de API aan."""
    waarde = maak_als_web()
    assert client.get("/api/v1/ik", headers=bearer(waarde) | KOPPEL).status_code == 200
    client.application.config["API_INGESCHAKELD"] = False
    r = client.get("/api/v1/ik", headers=bearer(waarde) | KOPPEL)
    assert (r.status_code, r.json) == (403, {"fout": "Geen toegang."})
    assert logregels("api.geweigerd")[0].gegevens["reden"] == "uit"


# Instellingen uit de omgeving: create_app leest ze zelf, de test zet app.config niet.


def app_uit_omgeving(monkeypatch, rol=API, **omgeving):
    from app import create_app

    for naam, waarde in omgeving.items():
        monkeypatch.setenv(naam, waarde)
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": rol})


@pytest.mark.parametrize("waarde,status", [("true", 200), ("false", 403)])
def test_api_aan_of_uit_via_de_omgeving(app, monkeypatch, waarde, status):
    """BLB-029 criteria 1 en 2: API_INGESCHAKELD uit de omgeving."""
    token = maak()
    api_app = app_uit_omgeving(monkeypatch, DIENST="api", API_INGESCHAKELD=waarde)
    with api_app.app_context():
        r = api_app.test_client().get("/api/v1/ik", headers=bearer(token) | KOPPEL)
        db.session.remove()
        db.engine.dispose()
    assert r.status_code == status


def test_eigen_koppelnet_uit_de_omgeving_is_de_standaardwhitelist(app, monkeypatch):
    web = app_uit_omgeving(monkeypatch, WEB, KOPPELNET="10.99.0.0/24")
    with web.app_context():
        maak()
        assert [str(n) for n in db.session.scalar(select(Token.ip_whitelist))] == ["10.99.0.0/24"]
        db.session.remove()
        db.engine.dispose()


@pytest.mark.parametrize("naam,waarde", [
    ("API_INGESCHAKELD", "ja"), ("API_INGESCHAKELD", "False"),
    ("KOPPELNET", "10.203.0.1/24"), ("KOPPELNET", "koppeling")])
def test_ongeldige_instelling_stopt_het_starten(monkeypatch, naam, waarde):
    with pytest.raises(ConfigFout, match=naam):
        app_uit_omgeving(monkeypatch, **{naam: waarde})


def test_web_kent_de_api_niet(client):
    """ADR-012: alleen de dienst api registreert /api/v1."""
    assert client.get("/api/v1/ik").status_code == 404
    assert not [r for r in client.application.url_map.iter_rules() if r.rule.startswith("/api")]


@pytest.mark.api
def test_api_kent_de_webinterface_niet(client):
    assert client.get("/inloggen").status_code == 404
    assert client.get("/health/live").json == {"status": "ok"}
    assert client.get("/health/ready").json == {"status": "ok"}


# Rechten in de database


@pytest.mark.api
@pytest.mark.parametrize("sql", [
    ("INSERT INTO token (naam, soort, prefix, hash, rechten, ip_whitelist, verloopt_op) VALUES "
     "('x', 'robot', 'AAAAAAAA', 'x', '{leden:importeren}', '{10.0.0.0/8}', now())"),
    "UPDATE token SET rechten = '{persoonsgegevens}'", "UPDATE token SET ingetrokken_op = NULL",
    "UPDATE token SET ip_whitelist = '{0.0.0.0/0}'", "DELETE FROM token",
    "DELETE FROM logregel", "UPDATE logregel SET actie = 'x'",
    # Sinds slice 6 maakt api leden aan en werkt ze bij (ADR-012), maar verwijdert niets.
    "DELETE FROM lid", "DELETE FROM taakrun", "UPDATE plaats SET boot_id = NULL"])
def test_api_rol_mag_tokens_niet_wijzigen(app, sql):
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(sql))
    db.session.rollback()


@pytest.mark.api
def test_api_rol_mag_laatst_gebruikt_bijwerken(app):
    db.session.execute(text("UPDATE token SET laatst_gebruikt_op = now()"))
    db.session.rollback()


# CLI (in web)


def test_cli_maakt_en_trekt_in(app):
    runner = app.test_cli_runner()
    r = runner.invoke(args=["token", "robot", "integratie", "--recht", "leden:importeren",
                            "--recht", "bootaantallen:lezen"])
    assert r.exit_code == 0, r.output
    waarde = r.stdout.strip()
    assert tokens.TOKEN.fullmatch(waarde) and "bewaar het nu" in r.stderr
    r = runner.invoke(args=["token", "intrekken", "integratie"])
    assert r.exit_code == 0 and "ingetrokken" in r.output
    assert [x.actie for x in db.session.scalars(select(Logregel).order_by(Logregel.id))] == [
        "token.gemaakt", "token.ingetrokken"]


@pytest.mark.parametrize("extra,melding", [
    ([], "minstens één recht"),
    (["--recht", "leden:importeren", "--dagen", "1096"], "1095 dagen"),
    (["--recht", "leden:importeren", "--whitelist", "10.203.0.1/24"], "Whitelist"),
])
def test_cli_weigert(app, extra, melding):
    """BLB-031 criterium 3, BLB-032 criterium 1, BLB-033 criterium 3."""
    r = app.test_cli_runner().invoke(args=["token", "robot", "integratie", *extra])
    assert r.exit_code == 1 and melding in r.output
    assert db.session.scalar(select(Token)) is None


# Contract (BLB-034 criterium 6, ADR-011)


def test_openapi_is_geldig_en_beschrijft_elke_route(app):
    validate(SPEC)
    from app import api

    with mock.patch.dict(os.environ, DIENST="api"):
        from app import create_app

        api_app = create_app({"TESTING": True})
    routes = {r.rule.removeprefix("/api/v1") for r in api_app.url_map.iter_rules()
              if r.endpoint.startswith(api.bp.name + ".")}
    assert routes == set(SPEC["paths"]) == {"/ik", "/leden", "/leden/importverzoek",
                                            "/leden/import-mislukt", "/bootaantallen"}
    voorbeeld = SPEC["paths"]["/ik"]["get"]["responses"]["200"]["content"]["application/json"]
    jsonschema.validate(voorbeeld["example"], SPEC["components"]["schemas"]["Ik"])
