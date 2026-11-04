"""Rekoverzicht (issue #87): welk plaatje en welke alt-tekst een vak krijgt, en de pagina."""

from pathlib import Path

import pytest

from app.domein import CLI, indeling, toewijzing
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot, soort
from tests.unit.test_web import inloggen

BOTEN = Path("app/web/static/boten")


def met_boot(code, soorten, bootsoort, club=False):
    p = plaats(code, [soort(s) for s in soorten], club)
    b = boot(None if club else lid().id, bootsoort)
    toewijzing.toewijzen(p.id, b.id, CLI)
    return p


def test_bezet_toont_de_soort_van_de_boot_niet_van_de_plaats(app):
    # Mutant: p.bootsoorten[0] in plaats van p.boot.bootsoort valt op bestand (kajak-bezet.jpg).
    p = met_boot("A/1/1", ["Kajak", "Canadese kano"], "Canadese kano")
    assert indeling.plaatje(p) == {
        "plaats_id": p.id, "bestand": "canadese-kano-bezet.jpg", "tekst": "", "club": False,
        "alt": "Plaats A/1/1, Canadese kano, bezet"}


def test_vrij_toont_de_eerste_soort_en_de_alt_noemt_alle_soorten(app):
    # De volgorde is die van de bootsoorten (id). Mutant: de laatste soort nemen valt op bestand;
    # alleen de eerste noemen valt op alt.
    v = indeling.plaatje(plaats("A/2/3", [soort("Surfski"), soort("Kajak")]))
    assert v["bestand"] == "kajak-vrij.jpg" and not v["club"]
    assert v["alt"] == "Plaats A/2/3, Kajak, Surfski, vrij"


def test_lege_clubplaats_is_vrij_met_stippelrand(app):
    # Mutant: club alleen op is_clubplaats (zonder `and not p.boot`) valt in het volgende geval.
    v = indeling.plaatje(plaats("A/1/1", [soort("Kajak")], club=True))
    assert v["bestand"] == "kajak-vrij.jpg" and v["club"]
    assert v["alt"] == "Plaats A/1/1, Kajak, clubplaats, leeg"


def test_clubplaats_met_clubboot_is_bezet_zonder_stippelrand(app):
    v = indeling.plaatje(met_boot("A/1/1", ["Kajak"], "Kajak", club=True))
    assert v["bestand"] == "kajak-bezet.jpg" and not v["club"]
    assert v["alt"] == "Plaats A/1/1, Kajak, clubplaats, bezet"


def test_plaats_zonder_bootsoort_is_een_leeg_vak(app):
    v = indeling.plaatje(indeling.rek_aanmaken("A", "", {(1, 1)}, CLI).plaatsen[0])
    assert v["bestand"] is None and v["tekst"] == ""
    assert v["alt"] == "Plaats A/1/1, geen bootsoort, vrij"


@pytest.mark.parametrize("naam, bestand", [("C11", "canadese-kano-vrij.jpg"),
                                           ("Surfski", "surfski-vrij.jpg")], ids=["c11", "surfski"])
def test_c11_gebruikt_het_plaatje_van_de_canadese_kano(app, naam, bestand):
    assert indeling.plaatje(plaats("A/1/1", [soort(naam)]))["bestand"] == bestand


def test_soort_zonder_plaatje_toont_de_naam_als_tekst(app):
    v = indeling.plaatje(plaats("A/1/1", [soort("Supboard")]))
    assert v["bestand"] is None and v["tekst"] == "Supboard"
    assert v["alt"] == "Plaats A/1/1, Supboard, vrij"


def test_elk_plaatje_uit_de_mapping_bestaat():
    for basis in indeling.PLAATJES.values():
        for variant in ("bezet", "vrij"):
            assert (BOTEN / f"{basis}-{variant}.jpg").is_file()


def test_rekoverzicht_zet_elke_plaats_op_verdieping_en_vak(app):
    p = plaats("A/2/3")
    plaats("A/1/1")
    assert indeling.rekoverzicht(p.rek).keys() == {(1, 1), (2, 3)}


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def test_pagina_vraagt_inloggen(client):
    r = client.get("/rekoverzicht")
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_menu_item_rekoverzicht(ingelogd):
    assert '<a href="/rekoverzicht">Rekoverzicht</a>' in ingelogd.get("/").text


def test_pagina_toont_per_plaats_een_plaatje_met_alt(ingelogd):
    p = met_boot("A/1/1", ["Kajak"], "Kajak")
    vrij = plaats("A/1/2", [soort("Supboard")])
    tekst = ingelogd.get("/rekoverzicht").text
    assert f'href="/plaatsen/{p.id}"' in tekst
    assert 'src="/static/boten/kajak-bezet.jpg" alt="Plaats A/1/1, Kajak, bezet"' in tekst
    assert f'href="/plaatsen/{vrij.id}"' in tekst
    assert "Plaats A/1/2, Supboard, vrij</span>" in tekst
