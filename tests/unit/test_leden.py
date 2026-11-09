"""Import van leden via PUT /api/v1/leden, met tests/fixtures/leden.json en eigen records als
nepbron (BLB-006, 007, 008, 024, 032, 034; ADR-004, ADR-012). Draait als de dienst api."""

import json
from datetime import date, timedelta
from pathlib import Path

import jsonschema
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import ProgrammingError

from app.domein import CLI, Regelfout, boten, leden, toewijzing, vandaag, wachtlijst
from app.models import Lid, Logregel, Plaats, Taakrun, Token, Wachtlijst, db
from tests.unit.conftest import API, TAKEN
from tests.unit.hulp import als_web, plaats
from tests.unit.test_tokens import KOPPEL, SPEC, bearer, maak_als_web

pytestmark = pytest.mark.api  # alleen de dienst api schrijft leden (ADR-012)

FIXTURE = json.loads((Path(__file__).parents[1] / "fixtures/leden.json").read_text())


def record(nummer, **velden):
    return {"lidnummer": nummer, "naam": f"Lid {nummer}",
            "lid_sinds": "2020-01-01", "opzegdatum": None} | velden


@pytest.fixture
def importeer(client):
    """PUT /api/v1/leden met een token met leden:importeren; geeft het antwoord."""
    waarde = maak_als_web()

    def put(lijst, **lichaam):
        return client.put("/api/v1/leden", headers=bearer(waarde) | KOPPEL,
                          **(lichaam or {"json": {"leden": lijst}}))
    put.token = waarde
    return put


def alle():
    db.session.expire_all()
    return {lid.lidnummer: lid for lid in db.session.scalars(select(Lid))}


def runs():
    db.session.expire_all()
    return db.session.scalars(select(Taakrun).where(Taakrun.taak == leden.TAAK)
                              .order_by(Taakrun.id)).all()


def test_fixture_importeren_met_aantallen_volgens_het_contract(importeer):
    """BLB-006 criterium 1, BLB-007 criterium 1: de nepbron gaat door PUT /api/v1/leden."""
    r = importeer(FIXTURE)
    assert r.status_code == 200
    jsonschema.validate(r.json, SPEC["components"]["schemas"]["Importuitkomst"])
    assert r.json == {"ontvangen": 210, "nieuw": 208, "bijgewerkt": 0, "uit_bron": 0,
                      "ongeldig": 0, "overgeslagen": 2}  # 2 langer dan 5 jaar opgezegd
    assert len(alle()) == 208
    [run] = runs()
    assert (run.status, run.aantallen["nieuw"]) == ("geslaagd", 208)


def test_nieuwe_en_gewijzigde_leden_op_lidnummer_met_alle_velden(importeer):
    importeer([record("1"), record("2")])
    r = importeer([record("1", naam="Nieuwe naam", opzegdatum="2099-01-01"), record("2"),
                   record("3")])
    assert r.json | {"ontvangen": 0} == {"ontvangen": 0, "nieuw": 1, "bijgewerkt": 1,
                                         "uit_bron": 0, "ongeldig": 0, "overgeslagen": 0}
    lid = alle()["1"]
    assert (lid.naam, str(lid.lid_sinds), str(lid.opzegdatum)) == (
        "Nieuwe naam", "2020-01-01", "2099-01-01")


def test_contactgegevens_in_een_record_worden_genegeerd_en_niet_bewaard(importeer):
    """#180: adres, telefoon en e-mail bestaan niet meer. Een record dat ze nog stuurt, blijft
    geldig (ook met een ongeldig e-mailadres) en de waarden worden nergens bewaard."""
    r = importeer([record("1", adres="Proefweg 1", telefoon="06-00000000", email="geen-adres")])
    assert (r.status_code, r.json["nieuw"], r.json["ongeldig"]) == (200, 1, 0)
    lid = alle()["1"]
    assert not {"adres", "telefoon", "email"} & set(Lid.__table__.columns.keys())
    assert not any(hasattr(lid, v) for v in ("adres", "telefoon", "email"))


def test_geen_logregel_per_lid_of_per_import(importeer):
    """BLB-024 criterium 2 en issue #21: een import die leden aanmaakt, wijzigt en oud-lid maakt,
    schrijft geen logregel. Mutaties aan boten door de import wel: zie de volgende test (#27)."""
    importeer([record("1"), record("2")])
    importeer([record("1", naam="Geheimnaam"), record("3")])
    assert db.session.scalars(select(Logregel.actie)).all() == ["token.gemaakt"]


def test_ongeldige_records_overgeslagen_rest_verwerkt(importeer):
    """BLB-006 criterium 4: ongeldig telt, zonder de inhoud te loggen."""
    importeer([record("1"), record("2")])
    r = importeer([
        record("1", lid_sinds="31-12-2020"),  # bestaand lid met tikfout: blijft lid, ongewijzigd
        record("2"), record(None), {"naam": "Zonder nummer"}, record(""), record("4", naam=" "),
        record("5", lid_sinds="31-12-2020"), record("6", naam=7), "geen record", record("2"),
        record("7", naam="x" * 300),
    ])
    assert (r.json["ongeldig"], r.json["nieuw"], r.json["uit_bron"]) == (9, 1, 0)
    lid = alle()
    assert str(lid["1"].lid_sinds) == "2020-01-01" and lid["1"].uit_bron_op is None
    assert set(lid) == {"1", "2", "7"} and len(lid["7"].naam) == 100
    assert "Zonder nummer" not in json.dumps([r.aantallen for r in runs()])


def test_nul_teken_maakt_het_record_ongeldig(importeer):
    """#74: PostgreSQL weigert NUL in tekst; het record telt als ongeldig, de rest gaat door."""
    r = importeer([record("1", naam="Proef\x00naam"), record("2")])
    assert r.status_code == 200 and (r.json["ongeldig"], r.json["nieuw"]) == (1, 1)
    assert set(alle()) == {"2"}


def test_ontbrekend_lid_wordt_oud_lid_met_importdatum_en_komt_terug(importeer):
    """BLB-008 criterium 2."""
    importeer([record("1"), record("2")])
    assert importeer([record("1"), record("3")]).json["uit_bron"] == 1
    twee = alle()["2"]
    assert twee.uit_bron_op == vandaag() and leden.is_oud_lid(twee) and twee.naam
    importeer([record("1"), record("2"), record("3")])
    assert alle()["2"].uit_bron_op is None


def test_halve_lijst_409_zonder_wijziging_en_als_mislukte_run(importeer):
    """BLB-034 criterium 3, BLB-007 criterium 4. Precies de helft gaat wel door."""
    importeer([record(str(n)) for n in range(1, 11)])
    r = importeer([record(str(n), naam="Anders") for n in range(1, 5)])
    assert r.status_code == 409 and "minder dan de helft" in r.json["fout"]
    assert all(lid.uit_bron_op is None and lid.naam != "Anders" for lid in alle().values())
    assert runs()[-1].status == "mislukt" and "minder dan de helft" in runs()[-1].foutmelding
    assert importeer([record(str(n)) for n in range(1, 6)]).json["uit_bron"] == 5


@pytest.mark.parametrize("lichaam", [{"json": {"leden": "geen lijst"}}, {"json": {}},
                                     {"json": [record("1")]}, {"data": "{kapot"},
                                     {"json": {"leden": [record("1")] * 5001}}],
                         ids=["tekst", "zonder-leden", "lijst-zonder-object", "kapot",
                              "5001-records"])
def test_geen_lijst_of_te_veel_records_422_zonder_wijziging(importeer, lichaam):
    """BLB-007 criterium 3. 5000 records mag wel (volgende test)."""
    importeer([record("1")])
    r = importeer(None, content_type="application/json", **lichaam)
    assert r.status_code == 422 and r.json["fout"].startswith("leden moet een lijst")
    assert set(alle()) == {"1"} and len(runs()) == 1


def test_5000_records_mag(importeer):
    assert importeer([record(str(n)) for n in range(5000)]).json["nieuw"] == 5000


def test_boven_2_mb_413_zonder_wijziging(importeer):
    """BLB-007 criterium 3; boven 3 MB weigert Traefik al (E2E)."""
    groot = [record(str(n), naam="x" * 500) for n in range(4000)]
    assert len(json.dumps({"leden": groot})) > 2 * 1024 * 1024  # zonder de grens geldig
    r = importeer(groot)
    assert r.status_code == 413 and r.json == {"fout": "Het verzoek is groter dan 2 MB."}
    assert alle() == {} and runs() == []


def test_zonder_recht_403_zonder_wijziging(client):
    """BLB-032 criterium 2."""
    waarde = maak_als_web(rechten=["bootaantallen:lezen"])
    for methode, pad, gegevens in [("put", "/leden", {"leden": [record("1")]}),
                                   ("get", "/leden/importverzoek", None),
                                   ("post", "/leden/import-mislukt", {"reden": "bron_onleesbaar"})]:
        r = getattr(client, methode)(f"/api/v1{pad}", json=gegevens,
                                     headers=bearer(waarde) | KOPPEL)
        assert (r.status_code, r.json) == (403, {"fout": "Geen toegang."})
    assert alle() == {} and runs() == []


def test_opzegging_maakt_oud_lid_met_behoud_van_gegevens_en_plaats(importeer):
    """BLB-008 criteria 1 en 5: gegevens en plaats blijven; een boot zonder plaats krijgt er
    geen meer. Rek, plaatsen en boten maakt web, zoals de beheerder."""
    importeer([record("1")])
    anna = alle()["1"].id

    def loods():
        p1, p2 = plaats("A/1/1", [1]), plaats("A/1/2", [1])
        b1 = boten.boot_aanmaken("Zeemeeuw", 1, anna, None, CLI)
        b2 = boten.boot_aanmaken("Fuut", 1, anna, None, CLI)
        toewijzing.toewijzen(p1.id, b1.id, CLI)
        return p1.id, p2.id, b1.id, b2.id

    p1, p2, b1, b2 = als_web(loods)
    gisteren = (vandaag() - timedelta(days=1)).isoformat()
    importeer([record("1", opzegdatum=gisteren)])
    lid = alle()["1"]
    assert leden.is_oud_lid(lid) and lid.naam == "Lid 1"
    assert als_web(lambda: db.session.get(Plaats, p1).boot_id) == b1
    with pytest.raises(Regelfout, match="is oud-lid"):
        als_web(lambda: toewijzing.toewijzen(p2, b2, CLI))


@pytest.mark.parametrize("oud", [True, False],
                         ids=["opzegdatum", "uit_de_bron"])
def test_boot_van_oud_lid_gaat_van_de_wachtlijst_met_het_token_als_actor(importeer, oud):
    """BLB-008 criterium 3 en #27 (BLB-024 criterium 2): de import haalt de boot van de lijst en
    schrijft een bootmutatie met de naam van het robottoken als actor. Boten van andere leden
    blijven staan."""
    importeer([record("1"), record("2")])
    anna, bram = alle()["1"].id, alle()["2"].id

    def op_lijst():
        b1 = boten.boot_aanmaken("Zeemeeuw", 1, anna, None, CLI)
        b2 = boten.boot_aanmaken("Fuut", 1, bram, None, CLI)
        wachtlijst.erop_zetten(b1.id, "2024-01-01", CLI)
        wachtlijst.erop_zetten(b2.id, "2024-01-01", CLI)
        return b1.id, b2.id

    b1, b2 = als_web(op_lijst)
    gisteren = (vandaag() - timedelta(days=1)).isoformat()
    lijst = [record("1", opzegdatum=gisteren)] if oud else []
    assert importeer(lijst + [record("2")]).status_code == 200
    assert als_web(lambda: [w.boot_id for _s, rij in wachtlijst.lijsten() for w in rij]) == [b2]
    db.session.expire_all()
    assert db.session.get(Wachtlijst, b1) is None
    [r] = db.session.scalars(select(Logregel).where(Logregel.actie == "wachtlijst.verwijderd"))
    token = db.session.scalar(select(Token))  # het enige token: dat van de import
    assert (r.actor_soort, r.actor_id, r.actor_naam) == ("token", token.id, token.naam)
    assert r.verwijzingen == [f"boot:{b1}", f"lid:{anna}"]
    assert r.gegevens == {"boot": "Zeemeeuw", "aangemeld_op": "2024-01-01", "reden": "oud-lid"}
    # Het lid zelf staat nog steeds niet in het log (ADR-004 v2.1.0)
    assert {a for a in db.session.scalars(select(Logregel.actie))} == {
        "token.gemaakt", "boot.aangemaakt", "wachtlijst.toegevoegd", "wachtlijst.verwijderd"}


def test_import_haalt_boot_eraf_als_de_opzegdatum_inmiddels_verstreken_is(importeer, monkeypatch):
    """BLB-041 en BLB-008: de eerste import na de opzegdatum maakt het lid oud-lid, ook als de
    bron niets nieuws meldt."""
    morgen = vandaag() + timedelta(days=1)
    importeer([record("1", opzegdatum=morgen.isoformat())])
    anna = alle()["1"].id

    def op_lijst():
        b = boten.boot_aanmaken("Zeemeeuw", 1, anna, None, CLI)
        wachtlijst.erop_zetten(b.id, None, CLI)
        return b.id

    b = als_web(op_lijst)
    importeer([record("1", opzegdatum=morgen.isoformat())])
    assert db.session.get(Wachtlijst, b) is not None
    monkeypatch.setattr(leden, "vandaag", lambda: morgen)
    importeer([record("1", opzegdatum=morgen.isoformat())])
    db.session.expire_all()
    assert db.session.get(Wachtlijst, b) is None


def test_opgeschoond_oud_lid_komt_niet_terug(importeer):
    """BLB-008 criterium 4. Precies 5 jaar geleden opgezegd komt nog binnen; een dag eerder niet."""
    grens = leden.jaren_terug(vandaag(), leden.BEWAARJAREN)
    r = importeer([record("1", opzegdatum=grens.isoformat()),
                   record("2", opzegdatum=(grens - timedelta(days=1)).isoformat())])
    assert r.json["overgeslagen"] == 1 and set(alle()) == {"1"}


def test_opzegdatum_in_de_toekomst_blijft_lid_tot_die_datum(importeer):
    """BLB-041 criteria 1 en 2."""
    morgen = vandaag() + timedelta(days=1)
    importeer([record("1", opzegdatum=morgen.isoformat())])
    lid = alle()["1"]
    assert not leden.is_oud_lid(lid) and leden.is_oud_lid(lid, morgen)


def test_jaren_terug_op_schrikkeldag():
    assert leden.jaren_terug(date(2028, 2, 29), 5) == date(2023, 2, 28)


# Importverzoek en gemelde fout


def test_verzoek_van_de_beheerder_krijgt_de_uitkomst_van_de_import(importeer, client):
    """BLB-006 criterium 5: het verzoek uit web staat open tot de import het afsluit."""
    verzoek = client.get("/api/v1/leden/importverzoek", headers=bearer(importeer.token) | KOPPEL)
    assert verzoek.json == {"aangevraagd": False}
    als_web(leden.import_aanvragen, CLI)
    verzoek = client.get("/api/v1/leden/importverzoek", headers=bearer(importeer.token) | KOPPEL)
    jsonschema.validate(verzoek.json, SPEC["components"]["schemas"]["Importverzoek"])
    assert verzoek.json == {"aangevraagd": True}
    importeer([record("1")])
    [run] = runs()
    assert run.status == "geslaagd" and run.aangevraagd_op and run.aantallen["nieuw"] == 1
    assert client.get("/api/v1/leden/importverzoek",
                      headers=bearer(importeer.token) | KOPPEL).json == {"aangevraagd": False}


@pytest.mark.parametrize("reden", list(leden.REDENEN))
def test_gemelde_fout_met_vaste_reden_sluit_het_verzoek(importeer, client, reden):
    """BLB-006 criterium 3: de ledenlijst blijft ongewijzigd, de vaste tekst staat in taakrun."""
    importeer([record("1")])
    als_web(leden.import_aanvragen, CLI)
    r = client.post("/api/v1/leden/import-mislukt", json={"reden": reden},
                    headers=bearer(importeer.token) | KOPPEL)
    assert (r.status_code, r.json) == (201, {})
    run = runs()[-1]
    assert (run.status, run.foutmelding) == ("mislukt", leden.REDENEN[reden]) and run.aangevraagd_op
    assert set(alle()) == {"1"}
    assert [r.actie for r in db.session.scalars(select(Logregel))] == ["token.gemaakt",
                                                                       "leden.import_aangevraagd"]


@pytest.mark.parametrize("gegevens", [{"reden": "De bron zegt: Anna woont op Proefweg 1"},
                                      {"reden": ["bron_onleesbaar"]}, {}, "bron_onleesbaar"],
                         ids=["vrije-tekst", "lijst", "leeg", "geen-object"])
def test_andere_reden_422_zonder_run(importeer, client, gegevens):
    r = client.post("/api/v1/leden/import-mislukt", json=gegevens,
                    headers=bearer(importeer.token) | KOPPEL)
    assert r.status_code == 422 and runs() == []


def test_lopende_import_geeft_409_en_verandert_niets(importeer):
    """BLB-006 criterium 6. Een andere sessie houdt de advisory lock van de import vast."""
    importeer([record("1")])
    engine = create_engine(API)
    with engine.connect() as lopend:
        lopend.execute(text("SELECT pg_advisory_lock(:slot)"), {"slot": leden.IMPORT_SLOT})
        r = importeer([record("1", naam="Tweede"), record("2")])
        lopend.execute(text("SELECT pg_advisory_unlock(:slot)"), {"slot": leden.IMPORT_SLOT})
    engine.dispose()
    assert (r.status_code, r.json) == (409, {"fout": "Er loopt al een import."})
    assert set(alle()) == {"1"} and alle()["1"].naam == "Lid 1" and len(runs()) == 1


# Databaserechten


@pytest.mark.parametrize("sql", ["INSERT INTO lid (lidnummer, naam) VALUES ('9', 'X')",
                                 "UPDATE lid SET naam = 'X'"])
def test_worker_maakt_of_wijzigt_geen_leden(database, sql):
    """ADR-012: alleen botenloods_api schrijft leden; de worker houdt DELETE voor de opschoning."""
    engine = create_engine(TAKEN)
    with engine.connect() as c, pytest.raises(ProgrammingError, match="permission denied"):
        c.execute(text(sql))
    with engine.begin() as c:
        c.execute(text("DELETE FROM lid WHERE false"))
    engine.dispose()
