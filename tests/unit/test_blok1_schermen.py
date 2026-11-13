"""Blok 1 van het nieuwe ontwerp (issue #150): het menu in vier groepen (BV-76), de plaats in twee kolommen,
de indeling in panelen. Gebruikersinvoer blijft geëscapet."""

import re

import pytest

from app.domein import CLI, indeling, toewijzing
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot, soort
from tests.unit.test_web import inloggen

GROEPEN = {
    "Dagelijks": ["Rekoverzicht", "Vrije plaatsen", "Wachtlijst", "Boten zonder eigenaar", "Gaan opzeggen"],
    "Lijsten": ["Boten", "Leden", "Opgezegd", "Log"],
    "Beheer": ["Indeling", "Kaartjes", "Import/export", "Beheerders", "Technisch log", "Tokens", "Instellingen", "Status"],
    "Account": ["Profiel", "Uitloggen"],
}


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def test_menu_heeft_vier_groepen_met_elk_hun_items_in_de_volgorde_van_het_ontwerp(ingelogd):
    # Mutant: een item in een andere groep of een andere volgorde valt hier.
    tekst = ingelogd.get("/rekoverzicht").text
    blokken = re.findall(r'<p class="bl-nav__groep" id="(menu-\d)">(\w+)</p>\s*<ul[^>]*aria-labelledby="(menu-\d)"[^>]*>(.*?)</ul>', tekst, re.DOTALL)
    assert {g: re.findall(r">([^<>]+)</(?:a|button)>", rest) for _, g, _, rest in blokken} == GROEPEN
    assert [g for _, g, _, _ in blokken] == list(GROEPEN)
    # Elke lijst verwijst naar de kop van zijn eigen groep.
    assert all(kop == lijst for kop, _, lijst, _ in blokken) and len({k for k, *_ in blokken}) == 4
    assert tekst.count('aria-labelledby="menu-') == 4


def test_menu_markeert_de_huidige_pagina_en_alleen_die(ingelogd):
    # Mutant: aria-current altijd zetten of nooit zetten valt hier.
    assert tekst_met_current(ingelogd, "/rekoverzicht") == ["Rekoverzicht"]
    assert tekst_met_current(ingelogd, "/indeling") == ["Indeling"]
    assert tekst_met_current(ingelogd, "/import-export") == ["Import/export"]
    assert tekst_met_current(ingelogd, "/tokens/nieuw") == []


def tekst_met_current(client, pad):
    return re.findall(r'aria-current="page">([^<]+)</a>', client.get(pad).text)


def test_melding_staat_in_een_blok_met_de_rol_op_de_tekst(ingelogd):
    r = ingelogd.post("/rekken", data={"naam": "A", "vak": ["1-1"]}, follow_redirects=True)
    assert '<div class="bl-meldingen">' in r.text
    assert re.search(r'<div class="ds-notice__body" role="status">[^<]*aangemaakt', r.text)


def test_plaats_toont_gegevens_en_wijzigen_in_twee_kolommen_met_panelen(ingelogd):
    p = plaats("A/1/1", [soort("Kajak")])
    tekst = ingelogd.get(f"/plaatsen/{p.id}").text
    assert tekst.count('<div class="bl-kolommen">') == 1
    assert tekst.index("Deze plaats is vrij") < tekst.index("Plaats wijzigen") < tekst.index("Openbare pagina")
    assert 'class="kaart"' not in tekst and tekst.count('<section class="dj-panel"') == 3


def test_plaats_escapet_boot_en_eigenaar_en_zet_vrijgeven_niet_primair(ingelogd):
    # Mutant: |safe op boot.naam of boot.lid.naam valt hier.
    p = plaats("A/1/1", [soort("Kajak")])
    toewijzing.toewijzen(p.id, boot(lid(naam="<i>Eva</i>").id, "Kajak", naam="<b>x</b>").id, CLI)
    tekst = ingelogd.get(f"/plaatsen/{p.id}").text
    assert "&lt;b&gt;x&lt;/b&gt;" in tekst and "&lt;i&gt;Eva&lt;/i&gt;" in tekst
    assert "<b>x</b>" not in tekst and "<i>Eva</i>" not in tekst
    assert '<button type="submit" class="ds-btn">Plaats A/1/1 vrijgeven</button>' in tekst


def test_indeling_toont_een_paneel_per_rek_met_status_in_een_tag_en_escapet(ingelogd):
    indeling.rek_aanmaken("<b>x<b>", "<i>y</i>", {(1, 1)}, CLI)
    plaats("A/1/1", [soort("Kajak")])
    tekst = ingelogd.get("/indeling").text
    assert "&lt;b&gt;x&lt;b&gt;" in tekst and "&lt;i&gt;y&lt;/i&gt;" in tekst
    assert "<b>x<b>" not in tekst and "<i>y</i>" not in tekst
    assert tekst.count('<span class="ds-tag">vrij</span>') == 2 and 'class="kaart"' not in tekst
    assert tekst.count("bl-uitklap__inhoud") == 2


# Import/export als eigen pagina (issue #262, BV-76)


def test_import_export_toont_drie_panelen_en_indeling_geen_import_of_export(ingelogd):
    # Mutant: de blokken terug in indeling.html, of een paneel weg uit import_export.html, valt hier.
    tekst = ingelogd.get("/import-export").text
    assert re.findall(r'<h2 class="dj-panel__title"[^>]*>([^<]+)</h2>', tekst) == [
        "Indeling als Excel", "Indeling als CSV", "Bezetting als CSV"]
    assert 'href="/indeling.xlsx"' in tekst and 'id="csv-bestand"' in tekst and 'id="bezetting-bestand"' in tekst
    assert "<h1>Import/export</h1>" in tekst and 'role="alert"' not in tekst
    indeling_tekst = ingelogd.get("/indeling").text
    for weg in ("/indeling.xlsx", "csv-bestand", "bezetting-bestand", "Indeling als CSV", "Bezetting als CSV",
                "Er loopt een bezettingsimport"):
        assert weg not in indeling_tekst


def test_import_export_vraagt_inloggen(client):
    r = client.get("/import-export")
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_menu_telt_boten_zonder_eigenaar_ook_op_import_export(ingelogd):
    # Mutant: het aantal uit het menu halen valt hier (BV-72).
    from tests.unit.test_eigenaar_onbekend import onbekend
    toewijzing.toewijzen(plaats("A/1/1").id, onbekend("Wulp").id, CLI)
    tekst = ingelogd.get("/import-export").text
    assert re.search(r'Boten zonder eigenaar <span class="ds-tag ds-tag--telling bl-nav__aantal">1</span>', tekst)
