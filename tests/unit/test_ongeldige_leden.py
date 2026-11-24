"""#381: de statuspagina toont de lidnummers van de ongeldige records uit de laatste ledenimport,
met een vaste reden, hooguit 10, alleen voor beheerders (een kijker krijgt 403: test_kijkers.py)."""

import logging

import pytest
from sqlalchemy import select

from app.domein import CLI, leden, opschonen
from app.models import Logregel, Taakrun, db
from tests.unit.hulp import als_api
from tests.unit.test_leden import importeer, record  # noqa: F401  (fixture)
from tests.unit.test_status_en_bootaantallen import run
from tests.unit.test_web_beheer import ingelogd as _ingelogd

ingelogd = _ingelogd  # fixture
TELLINGEN = {"ontvangen", "nieuw", "bijgewerkt", "uit_bron", "ongeldig", "overgeslagen"}


def imp(records):
    """De import zoals de dienst api hem draait; de statuspagina leest de web-app."""
    return als_api(leden.importeer, records, CLI)


def lijst(client):
    return client.get("/status.json").json["import"]["ongeldige_leden"]


@pytest.mark.parametrize("ongeldig, reden", [
    (record("1", naam=" "), "naam ontbreekt"),
    (record("1", lid_sinds="12-03-2019"), "datum niet als JJJJ-MM-DD"),
    (record("1", opzegdatum=20190312), "datum niet als JJJJ-MM-DD"),
    (record("1", naam="Proef\x00naam"), "ongeldige tekst"),
    (record("1", naam=7), "ongeldige tekst"),
    (record("1", naam="", lid_sinds="12-03-2019"), "datum niet als JJJJ-MM-DD"),  # volgorde: tekst, datum, naam
    (record("1", naam=7, lid_sinds="12-03-2019"), "ongeldige tekst"),
], ids=["naam", "datum-tekst", "datum-getal", "nul-teken", "naam-geen-tekst", "naam-en-datum", "tekst-en-datum"])
def test_elke_reden_staat_bij_het_lidnummer(ingelogd, ongeldig, reden):
    imp([record("2"), ongeldig])
    assert lijst(ingelogd) == {"lijst": [["1", reden]], "niet_getoond": 0, "zonder_lidnummer": 0}


def test_het_tweede_lidnummer_telt_als_dubbel_en_het_eerste_blijft_geldig(ingelogd):
    imp([record("1"), record("2"), record("1", naam="Andere")])
    assert lijst(ingelogd)["lijst"] == [["1", "lidnummer dubbel"]]


def test_zonder_bruikbaar_lidnummer_telt_alleen_als_zonder_lidnummer(ingelogd):
    imp([record("1"), record(None), {"naam": "Zonder"}, record(""), record("<b>x</b>"), "geen record"])
    assert lijst(ingelogd) == {"lijst": [], "niet_getoond": 0, "zonder_lidnummer": 5}
    html = ingelogd.get("/status").get_data(as_text=True)
    assert "5 zonder lidnummer" in html and "&lt;b&gt;" not in html and "<b>x</b>" not in html


@pytest.mark.parametrize("n, getoond, niet_getoond", [(9, 9, 0), (10, 10, 0), (11, 10, 1), (25, 10, 15)])
def test_hooguit_tien_lidnummers_in_de_volgorde_van_de_bron(ingelogd, n, getoond, niet_getoond):
    nummers = [str(900 - i) for i in range(n)]  # aflopend: afwijkend van de sortering
    imp([record("1")] + [record(x, naam="") for x in nummers])
    uit = lijst(ingelogd)
    assert [x[0] for x in uit["lijst"]] == nummers[:getoond]
    assert uit["niet_getoond"] == niet_getoond
    html = ingelogd.get("/status").get_data(as_text=True)
    assert (f"Nog {niet_getoond} ongeldige lidnummers" in html) == bool(niet_getoond)


def test_het_dubbele_nummer_telt_mee_voor_de_grens(ingelogd):
    imp([record(str(i)) for i in range(10)] + [record("0"), record("1")])
    uit = lijst(ingelogd)
    assert len(uit["lijst"]) == 2 and uit["niet_getoond"] == 0


def test_de_pagina_toont_nummer_en_reden_en_een_schone_import_wist_de_lijst(ingelogd):
    imp([record("1"), record("7", naam=""), record("8", lid_sinds="12-03-2019")])
    html = ingelogd.get("/status").get_data(as_text=True)
    assert "<li>7: naam ontbreekt</li>" in html and "<li>8: datum niet als JJJJ-MM-DD</li>" in html
    assert "ongeldige_leden" not in html  # niet als k: v in de tellingen
    imp([record("1"), record("7")])
    assert lijst(ingelogd) is None and "Ongeldige records" not in ingelogd.get("/status").get_data(as_text=True)


def test_het_importscherm_toont_de_lijst_niet_als_telling(ingelogd):  # #401: de runs staan bij Import/export
    imp([record("1"), record("7", naam="")])
    html = ingelogd.get("/import-export").get_data(as_text=True)
    assert "ongeldig: 1" in html and "ongeldige_leden" not in html and "naam ontbreekt" not in html


@pytest.mark.api
def test_het_api_antwoord_blijft_tellingen_zonder_lidnummers(importeer):  # noqa: F811
    r = importeer([record("1"), record("7", naam=""), record(None)])
    assert set(r.json) == TELLINGEN and r.json["ongeldig"] == 2
    assert all(type(v) is int for v in r.json.values())


@pytest.mark.api
def test_geen_lidnummer_van_een_ongeldig_record_in_de_log(importeer, caplog):  # noqa: F811
    with caplog.at_level(logging.DEBUG):
        importeer([record("1"), record("7777", naam=""), record("1")])
    assert "7777" not in caplog.text
    assert db.session.scalars(select(Logregel.actie)).all() == ["token.gemaakt"]


def test_een_run_van_voor_381_heeft_geen_lijst(ingelogd):
    run(leden.TAAK, "geslaagd", aantallen={"ongeldig": 3})
    assert lijst(ingelogd) is None


def runs_met_lijst():
    return [r.id for r in db.session.scalars(select(Taakrun).where(Taakrun.taak == leden.TAAK))
            if leden.ONGELDIGE_LEDEN in r.aantallen]


@pytest.mark.parametrize("daarna", ["schoon", "mislukt"])
def test_de_volgende_import_haalt_de_lidnummers_uit_eerdere_runs(ingelogd, daarna):
    imp([record("1"), record("7", naam="")])
    assert len(runs_met_lijst()) == 1
    if daarna == "schoon":
        imp([record("1"), record("7")])
    else:
        als_api(leden.import_mislukt, "bron_onbereikbaar")
    db.session.expire_all()
    assert runs_met_lijst() == [] and lijst(ingelogd) is None


def test_zonder_import_staat_er_null_en_de_opschoning_heeft_geen_lijst(ingelogd):
    run(opschonen.TAAK, "geslaagd")
    uit = ingelogd.get("/status.json").json
    assert uit["import"]["ongeldige_leden"] is None and "ongeldige_leden" not in uit["opschoning"]
