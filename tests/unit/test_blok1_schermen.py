"""Blok 1 van het nieuwe ontwerp (issue #150): het menu in drie groepen, de plaats in twee kolommen,
de indeling in panelen. Gebruikersinvoer blijft geëscapet."""

import re

import pytest

from app.domein import CLI, indeling, toewijzing
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot, soort
from tests.unit.test_web import inloggen

GROEPEN = {
    "Dagelijks": ["Rekoverzicht", "Indeling", "Vrije plaatsen", "Wachtlijst", "Gaan opzeggen", "Kaartjes"],
    "Registers": ["Boten", "Leden", "Opgezegd", "Log", "Technisch log"],
    "Beheer": ["Beheerders", "Tokens", "Instellingen", "Status", "Profiel", "Uitloggen"],
}


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def test_menu_heeft_drie_groepen_met_elk_hun_items_in_de_volgorde_van_het_ontwerp(ingelogd):
    # Mutant: een item in een andere groep of een andere volgorde valt hier.
    tekst = ingelogd.get("/rekoverzicht").text
    blokken = re.findall(r'<p class="bl-nav__groep" id="menu-\d">(\w+)</p>\s*<ul[^>]*>(.*?)</ul>', tekst, re.DOTALL)
    assert {g: re.findall(r">([^<>]+)</(?:a|button)>", rest) for g, rest in blokken} == GROEPEN
    assert [g for g, _ in blokken] == list(GROEPEN)
    assert tekst.count('aria-labelledby="menu-') == 3


def test_menu_markeert_de_huidige_pagina_en_alleen_die(ingelogd):
    # Mutant: aria-current altijd zetten of nooit zetten valt hier.
    assert tekst_met_current(ingelogd, "/rekoverzicht") == ["Rekoverzicht"]
    assert tekst_met_current(ingelogd, "/indeling") == ["Indeling"]
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
