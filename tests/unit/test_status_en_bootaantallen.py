"""Bootaantallen per lid in de lijst per lid en via GET /api/v1/bootaantallen (BLB-009, ADR-004,
ADR-012) en de technische statuspagina (BLB-037, ADR-010)."""

import os
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import jsonschema
import pytest
from sqlalchemy import select

from app.domein import CLI, boten, leden, opschonen, toewijzing, tokens, wachtlijst
from app.models import Logregel, Taakrun, Token, db
from tests.unit.conftest import WEB
from tests.unit.hulp import lid
from tests.unit.test_indeling_en_toewijzing import boot, plaats
from tests.unit.test_tokens import KOPPEL, SPEC, app_uit_omgeving, bearer, maak
from tests.unit.test_web_beheer import ingelogd as _ingelogd

ingelogd = _ingelogd  # fixture

NUL = {"Kajak": 0, "Canadese kano": 0, "Surfski": 0, "C11": 0, "Supboard": 0}


def loods():
    """Anna: kajak op een plaats, surfski op een plaats, kajak op de wachtlijst, kano zonder
    plaats. Bert: geen boten. Een clubboot op een clubplaats."""
    anna, bert = lid("1001", "Anna"), lid("1002", "Bert")
    plaats("A/1/1")
    toewijzing.toewijzen(plaats("A/1/2").id, boot(anna.id).id, CLI)
    toewijzing.toewijzen(plaats("A/1/3", ("Surfski",)).id,
                         boot(anna.id, "Surfski", "Pijl").id, CLI)
    wachtlijst.erop_zetten(boot(anna.id, naam="Reiger").id, None, CLI)
    boot(anna.id, "Canadese kano", "Bever")
    toewijzing.toewijzen(plaats("A/2/1", club=True).id, boot(None, naam="Clubkajak").id,
                         CLI)
    return anna, bert


VERWACHT = [{"lidnummer": "1001", "aantallen": NUL | {"Kajak": 1, "Surfski": 1}},
            {"lidnummer": "1002", "aantallen": NUL}]


def test_telregel_alleen_boten_met_plaats_zonder_clubboten(app):
    """BLB-009 criteria 3, 4 en 5: elke bootsoort, ook 0; de wachtende boot, de boot zonder
    plaats en de clubboot tellen niet."""
    loods()
    assert boten.bootaantallen() == VERWACHT


def test_lijst_per_lid_toont_dezelfde_aantallen(app, ingelogd):
    """BLB-009 criterium 2."""
    anna, bert = loods()
    html = ingelogd.get(f"/leden/{anna.id}").get_data(as_text=True)
    assert "Aantal boten per bootsoort" in html
    for soort, aantal in VERWACHT[0]["aantallen"].items():
        assert f'<td data-label="Bootsoort">{soort}</td><td data-label="Aantal">{aantal}</td>' in html
    assert '<td data-label="Aantal">1</td>' not in ingelogd.get(f"/leden/{bert.id}").get_data(
        as_text=True)


@pytest.fixture
def api(app, monkeypatch):
    return app_uit_omgeving(monkeypatch, DIENST="api").test_client()


def test_api_levert_dezelfde_aantallen_en_het_tijdstip(app, api):
    """BLB-009 criterium 3; BLB-037 criterium 1 (laatst opgehaald)."""
    loods()
    waarde = maak("integratie", ["bootaantallen:lezen"])
    r = api.get("/api/v1/bootaantallen", headers=bearer(waarde) | KOPPEL)
    assert r.status_code == 200 and r.json == VERWACHT == boten.bootaantallen()
    jsonschema.validate(r.json, SPEC["components"]["schemas"]["Bootaantallen"])
    db.session.expire_all()
    [run] = db.session.scalars(select(Taakrun).where(Taakrun.taak == boten.BOOTAANTALLEN)).all()
    assert run.aantallen == {"leden": 2}
    assert db.session.scalar(select(Token.laatst_gebruikt_op)) is not None


def test_api_zonder_recht_403_met_logregel(app, api):
    """BLB-009 criterium 6; het token van de import heeft het recht niet."""
    waarde = maak("integratie", ["leden:importeren"])
    r = api.get("/api/v1/bootaantallen", headers=bearer(waarde) | KOPPEL)
    assert (r.status_code, r.json) == (403, {"fout": "Geen toegang."})
    db.session.expire_all()
    [regel] = db.session.scalars(select(Logregel).where(Logregel.actie == "api.geweigerd")).all()
    assert regel.gegevens["reden"] == "zonder_recht"
    assert db.session.scalar(select(Taakrun.id)) is None


def test_openapi_voorbeeld_past_bij_het_schema():
    voorbeeld = SPEC["paths"]["/bootaantallen"]["get"]["responses"]["200"]["content"][
        "application/json"]["example"]
    jsonschema.validate(voorbeeld, SPEC["components"]["schemas"]["Bootaantallen"])


# Statuspagina


def run(taak, status="geslaagd", uren=1, **velden):
    eind = datetime.now(UTC) - timedelta(hours=uren)
    db.session.add(Taakrun(taak=taak, status=status, gestart_op=eind, beeindigd_op=eind, **velden))
    db.session.commit()


def json_status(client):
    r = client.get("/status.json")
    assert r.status_code == 200 and r.mimetype == "application/json"
    return r.json


def test_status_vraagt_inloggen(client):
    for pad in ("/status", "/status.json"):
        r = client.get(pad)
        assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_html_en_json_uit_dezelfde_gegevens(app, ingelogd):
    """BLB-037 criterium 1: alle onderdelen, en de opschoning met tijdstip en aantallen
    (BLB-026 criterium 5)."""
    run("heartbeat", uren=0)
    run(leden.TAAK, aantallen={"nieuw": 3, "bijgewerkt": 1})
    run(opschonen.TAAK, aantallen={"logregels": 7, "leden": 2, "boten": 3, "fotos": 1})
    s = json_status(ingelogd)
    assert s["status"] == "ok" and s["versie"] == os.environ.get("APP_VERSIE", "onbekend")
    assert s["database"]["status"] == "ok" and s["database"]["migratie"] == s["database"]["verwacht"]
    assert s["opschoning"]["aantallen"] == {"logregels": 7, "leden": 2, "boten": 3, "fotos": 1}
    assert s["api"] == {"status": "ok", "ingeschakeld": True}
    assert s["bootaantallen"]["laatst_opgehaald"] is None
    html = ingelogd.get("/status").get_data(as_text=True)
    assert 'href="/status">Status</a>' in html and 'href="/status.json"' in html
    assert all(t in html for t in ("logregels: 7", "leden: 2", "boten: 3", "fotos: 1", "nieuw: 3"))
    assert s["opschoning"]["tijdstip"] is not None and "Laatste opschoning: nog niet" not in html


@pytest.mark.parametrize("uren,status", [(25.9, "ok"), (26.1, "waarschuwing")],
                         ids=["jonger_dan_26_uur", "ouder_dan_26_uur"])
def test_import_ouder_dan_26_uur_geeft_waarschuwing(app, ingelogd, uren, status):
    """BLB-037 criterium 3, beide kanten van de grens."""
    run("heartbeat", uren=0)
    run(leden.TAAK, uren=uren)
    assert json_status(ingelogd)["import"]["status"] == status


def test_zonder_import_waarschuwing(app, ingelogd):
    s = json_status(ingelogd)
    assert s["import"]["status"] == "waarschuwing" and s["status"] == "waarschuwing"


def test_mislukte_import_met_reden_uit_de_vaste_lijst(app, ingelogd):
    """BLB-037 criterium 2."""
    run(leden.TAAK, uren=2)
    run(leden.TAAK, status="mislukt", foutmelding=leden.REDENEN["bron_onbereikbaar"])
    s = json_status(ingelogd)["import"]
    assert (s["status"], s["resultaat"], s["reden"]) == (
        "waarschuwing", "mislukt", "De ledenbron is niet bereikbaar.")
    assert "De ledenbron is niet bereikbaar." in ingelogd.get("/status").get_data(as_text=True)


@pytest.mark.parametrize("minuten,status", [(1, "ok"), (3, "waarschuwing")],
                         ids=["verse_heartbeat", "oude_heartbeat"])
def test_heartbeat_ouder_dan_2_minuten(app, ingelogd, minuten, status):
    run("heartbeat", uren=minuten / 60)
    assert json_status(ingelogd)["worker"]["status"] == status


def test_mislukte_opschoning_waarschuwing(app, ingelogd):
    run(opschonen.TAAK, status="mislukt", foutmelding="RuntimeError: de opschoning is mislukt.")
    assert json_status(ingelogd)["opschoning"]["status"] == "waarschuwing"


@pytest.mark.parametrize("dagen,gewaarschuwd", [(31, True), (32, False)],
                         ids=["verloopt_binnen_31_dagen", "verloopt_na_31_dagen"])
def test_waarschuwing_voor_token_dat_binnen_31_dagen_verloopt(app, ingelogd, dagen, gewaarschuwd):
    """BLB-037 criterium 5, beide kanten van de grens; een ingetrokken of al verlopen token telt
    niet, ook niet bij de robottokens."""
    maak("kort", ["bootaantallen:lezen"], dagen=dagen)
    maak("weg", ["bootaantallen:lezen"], dagen=1)
    tokens.intrekken("weg", CLI)
    maak("verlopen", ["bootaantallen:lezen"], dagen=1)
    db.session.scalar(select(Token).where(Token.naam == "verlopen")).verloopt_op = (
        datetime.now(UTC) - timedelta(days=1))
    db.session.commit()
    alles = json_status(ingelogd)
    assert [t["naam"] for t in alles["robottokens"]["tokens"]] == ["kort"]
    s = alles["tokens_verlopen"]
    if not gewaarschuwd:
        assert s == {"status": "ok", "tokens": []}
        return
    datum = (datetime.now(UTC) + timedelta(days=dagen)).astimezone(ZoneInfo(app.config["TZ"])).date()
    assert s["status"] == "waarschuwing" and [t["naam"] for t in s["tokens"]] == ["kort"]
    html = ingelogd.get("/status").get_data(as_text=True)
    assert "kort (robot), vervalt op" in html and "weg (robot)" not in html
    assert "verlopen (robot)" not in html
    assert s["tokens"][0]["vervaldatum"] == datum.isoformat()


def test_geen_tokens_wachtwoorden_of_ledengegevens(app, ingelogd):
    """BLB-037 criterium 4; de laatste aanroep per robottoken staat er wel (criterium 1)."""
    lid("1001", "Anna Geheimnaam")
    waarde = maak("integratie", ["leden:importeren"])
    token = db.session.scalar(select(Token))
    token.laatst_gebruikt_op = datetime.now(UTC)
    db.session.commit()
    s = json_status(ingelogd)
    assert [t["naam"] for t in s["robottokens"]["tokens"]] == ["integratie"]
    assert s["robottokens"]["tokens"][0]["laatste_aanroep"] is not None
    for pagina in (ingelogd.get("/status.json"), ingelogd.get("/status")):
        tekst = pagina.get_data(as_text=True)
        for geheim in (waarde, token.prefix, token.hash, "Geheimnaam", "Proefweg",
                       "06-00001234", "@example.org"):
            assert geheim not in tekst


def test_versie_en_api_uit_de_omgeving(database, monkeypatch):
    """ADR-010: de versie komt uit APP_VERSIE (buildargument); web leest API_INGESCHAKELD."""
    web = app_uit_omgeving(monkeypatch, rol=WEB, APP_VERSIE="1.2.3", API_INGESCHAKELD="false")
    assert (web.config["APP_VERSIE"], web.config["API_INGESCHAKELD"]) == ("1.2.3", False)
    with web.app_context():
        from app.domein import status

        s = status.status()
    assert (s["versie"], s["api"]["ingeschakeld"]) == ("1.2.3", False)
