"""Slice 10: de vier leesaanroepen van de API (ADR-012 v1.6.0; BLB-032 criterium 3, BLB-034
criteria 2 en 3). De gegevens maakt web; de aanroepen draaien als de dienst api."""

import secrets
from datetime import date

import jsonschema
import pytest

from app.domein import CLI, toewijzing, wachtlijst
from app.models import db
from tests.unit.hulp import lid
from tests.unit.test_indeling_en_toewijzing import boot, plaats
from tests.unit.test_tokens import KOPPEL, SPEC, app_uit_omgeving, bearer, eigenaar, maak

ROUTES = {"/plaatsen": ("plaatsen:lezen", "Plaatsen"), "/boten": ("boten:lezen", "Boten"),
          "/leden": ("leden:lezen", "Leden"), "/wachtlijst": ("wachtlijst:lezen", "Wachtlijst")}


@pytest.fixture
def api(app, monkeypatch):
    return app_uit_omgeving(monkeypatch, DIENST="api").test_client()


def schema(naam):
    """Een schema uit openapi.yaml met de componenten erbij, zodat $ref werkt."""
    return {"$ref": f"#/components/schemas/{naam}", "components": SPEC["components"]}


def loods():
    """Rek A met A/1/1 (Zeemeeuw van Anna) en clubplaats A/2/1 (Clubkajak); rek B met een lege B/1/1.
    Op de wachtlijst: Reiger van Bert (kajak, eerder) en Pijl van Anna (kajak, later), Bever van
    Anna (kano) en Mus van oud-lid Carla, die niet meetelt."""
    anna = lid("1002", "Anna", lid_sinds=date(2020, 4, 1))
    bert = lid("1001", "Bert")
    carla = lid("1003", "Carla")
    toewijzing.toewijzen(plaats("A/1/1", ("Kajak", "Surfski")).id, boot(anna.id).id, CLI)
    toewijzing.toewijzen(plaats("A/2/1", club=True).id, boot(None, naam="Clubkajak").id, CLI)
    plaats("B/1/1")
    wachtlijst.erop_zetten(boot(anna.id, naam="Pijl").id, "2026-02-01", CLI)
    wachtlijst.erop_zetten(boot(bert.id, naam="Reiger").id, "2026-01-01", CLI)
    wachtlijst.erop_zetten(boot(anna.id, "Canadese kano", "Bever").id, "2025-06-01", CLI)
    wachtlijst.erop_zetten(boot(carla.id, naam="Mus").id, "2020-01-01", CLI)
    eigenaar("UPDATE lid SET opzegdatum = '2021-01-01' WHERE lidnummer = '1003'")
    db.session.expire_all()


def lees(api, pad, *rechten):
    waarde = maak(f"lees-{secrets.token_hex(4)}", list(rechten))
    return api.get(f"/api/v1{pad}", headers=bearer(waarde) | KOPPEL)


@pytest.mark.parametrize("pad", list(ROUTES))
def test_elke_leesroute_vraagt_haar_recht(app, api, pad):
    """403 met een token met alle andere rechten; 200 en het schema uit openapi.yaml met het
    eigen recht."""
    loods()
    recht, naam = ROUTES[pad]
    anders = [r for r, _ in ROUTES.values() if r != recht]
    r = lees(api, pad, *anders)
    assert (r.status_code, r.json) == (403, {"fout": "Geen toegang."})
    r = lees(api, pad, recht)
    assert r.status_code == 200 and r.headers["Cache-Control"] == "no-store"
    jsonschema.validate(r.json, schema(naam))


def test_plaatsen_in_de_volgorde_van_het_overzicht(app, api):
    loods()
    assert lees(api, "/plaatsen", "plaatsen:lezen").json == [
        {"code": "A/1/1", "rek": "A", "clubplaats": False, "bootsoorten": ["Kajak", "Surfski"],
         "boot": {"id": 1, "naam": "Zeemeeuw"}},
        {"code": "A/2/1", "rek": "A", "clubplaats": True, "bootsoorten": ["Kajak"],
         "boot": {"id": 2, "naam": "Clubkajak"}},
        {"code": "B/1/1", "rek": "B", "clubplaats": False, "bootsoorten": ["Kajak"],
         "boot": None}]


def test_boten_met_eigenaar_alleen_naam_en_lidnummer(app, api):
    """BLB-032 criterium 3 (#180): naam en lidnummer, geen adres, telefoon of e-mail."""
    loods()
    rijen = {b["naam"]: b for b in lees(api, "/boten", "boten:lezen").json}
    assert [b["naam"] for b in lees(api, "/boten", "boten:lezen").json] == sorted(rijen)
    assert rijen["Zeemeeuw"] == {"id": 1, "naam": "Zeemeeuw", "bootsoort": "Kajak",
                                 "plaats": "A/1/1", "eigenaar": {"lidnummer": "1002", "naam": "Anna"},
                                 "clubboot": False}
    assert rijen["Clubkajak"]["eigenaar"] is None and rijen["Clubkajak"]["clubboot"] is True and rijen["Pijl"]["plaats"] is None


def test_leden_op_lidnummer_met_lid_sinds_en_opzegdatum_voor_leden_lezen(app, api):
    """#180: lid sinds en opzegdatum komen mee met leden:lezen, zonder ander recht."""
    loods()
    leden = lees(api, "/leden", "leden:lezen").json
    assert leden == [
        {"lidnummer": "1001", "naam": "Bert", "oud_lid": False, "lid_sinds": None, "opzegdatum": None},
        {"lidnummer": "1002", "naam": "Anna", "oud_lid": False, "lid_sinds": "2020-04-01",
         "opzegdatum": None},
        {"lidnummer": "1003", "naam": "Carla", "oud_lid": True, "lid_sinds": None,
         "opzegdatum": "2021-01-01"}]


def test_wachtlijst_per_bootsoort_langst_wachtend_eerst_zonder_oud_leden(app, api):
    loods()
    rijen = lees(api, "/wachtlijst", "wachtlijst:lezen").json
    assert [(r["bootsoort"], r["boot"]["naam"], r["aangemeld_op"]) for r in rijen] == [
        ("Canadese kano", "Bever", "2025-06-01"), ("Kajak", "Reiger", "2026-01-01"),
        ("Kajak", "Pijl", "2026-02-01")]
    assert rijen[1]["eigenaar"] == {"lidnummer": "1001", "naam": "Bert"}


def test_openapi_voorbeelden_passen_bij_de_schemas():
    for pad, (_recht, naam) in ROUTES.items():
        inhoud = SPEC["paths"][pad]["get"]["responses"]["200"]["content"]["application/json"]
        voorbeelden = [inhoud["example"]] if "example" in inhoud else [
            v["value"] for v in inhoud["examples"].values()]
        for voorbeeld in voorbeelden:
            jsonschema.validate(voorbeeld, schema(naam))


def test_onbekend_pad_en_verkeerde_methode_geven_json(api, client):
    """#68: 404 en 405 in het foutformaat van de API; web houdt zijn eigen pagina."""
    r = api.get("/api/v1/bestaatniet")
    assert r.status_code == 404 and r.json == {"fout": "Onbekend pad."}
    r = api.delete("/api/v1/plaatsen")
    assert r.status_code == 405 and r.json == {"fout": "Deze methode kan niet op dit pad."}
    assert "GET" in r.headers["Allow"] and "DELETE" not in r.headers["Allow"]
    assert client.get("/bestaatniet").content_type.startswith("text/html")


@pytest.mark.parametrize("pad", ["/api/v1/%2Fik", "/api/v1/ik%2F", "/api%2Fv1/ik", "/api/v1/%61k"])
def test_gecodeerd_pad_geeft_json(api, client, pad):
    """#133: de 400 op procentcodering in het foutformaat van de API; web houdt zijn eigen pagina."""
    r = api.get(pad)
    assert r.status_code == 400 and r.json == {"fout": "Ongeldig verzoek."}
    assert client.get(pad).content_type.startswith("text/html")


def test_nul_teken_geeft_json(api):
    r = api.get("/api/v1/ik?x=%00")
    assert r.status_code == 400 and r.json == {"fout": "Ongeldig verzoek."}


@pytest.mark.parametrize("methode, pad", [("put", "/api/v1/bestaatniet"), ("post", "/api/v1/ik")])
def test_te_groot_op_pad_zonder_view_geeft_json(api, methode, pad):
    """#91: ook zonder view de 413 van de API, niet de HTML van werkzeug."""
    r = getattr(api, methode)(pad, data=b"x" * (2 * 1024 * 1024 + 1), content_type="application/json")
    assert r.status_code == 413 and r.json == {"fout": "Het verzoek is groter dan 2 MB."}
