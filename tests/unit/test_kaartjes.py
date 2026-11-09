"""Kaartjes met QR-code (BLB-021, BLB-027 criteria 1 en 2 deel kaartjes, ADR-011, ADR-003)."""

import re

import pytest
import segno

from app.domein import CLI, indeling, instellingen, toewijzing
from tests.unit.hulp import logo_zetten
from tests.unit.test_indeling_en_toewijzing import boot, plaats
from tests.unit.test_overzichten_en_instellingen import loods
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture


def kaartjes(tekst):
    """{plaatscode: html van het kaartje}."""
    return dict(re.findall(r'<section class="kaartje" aria-label="Kaartje ([^"]+)">(.*?)</section>',
                           tekst, re.DOTALL))


def qr_pad(html):
    return re.search(r'<svg[^>]*class="qr-kaartje".*? d="([^"]+)"', html, re.DOTALL).group(1)


def qr_van(url):
    """Het pad van de QR-code die segno voor url maakt; gelijk pad is gelijke modules."""
    return qr_pad(segno.make(url, error="m").svg_inline(svgclass="qr-kaartje"))


def test_kaartje_met_logo_code_bootsoort_en_qr_naar_openbare_pagina(app, ingelogd):  # noqa: F811
    kenmerk = logo_zetten()
    _vrij, bezet, _club, _c11, _anna = loods()
    indeling.rek_wijzigen(bezet.rek_id, "A", "Grote botenloods stelling links", CLI)
    r = ingelogd.get(f"/kaartjes/print?plaats={bezet.id}")
    assert r.status_code == 200
    kaart = kaartjes(r.text)["A/1/2"]
    assert f'src="/logo/{kenmerk}"' in kaart and ">A/1/2<" in kaart
    assert '<p class="kaartje-soorten">Geschikt voor Kajak</p>' in kaart
    assert qr_pad(kaart) == qr_van(f"http://localhost:8080/p/{bezet.publieke_sleutel}")
    # Geen eigenaar en geen omschrijving van het rek (issue #143); geen lidnummer of boot
    # (overlay §8); de QR-code zelf zonder tekst.
    for verboden in ("Anna de Vries", "Grote botenloods", "1001", "Zeemeeuw"):
        assert verboden not in r.text
    assert "<title" not in kaart.split("<svg", 1)[1]


def test_bootsoorten_op_id_zonder_eigenaar_vrij_of_vereniging(ingelogd):  # noqa: F811
    _vrij, _bezet, club, _c11, _anna = loods()
    zonder = indeling.rek_aanmaken("B", "", {(1, 1)}, CLI)  # een nieuw vak heeft geen bootsoort
    toewijzing.toewijzen(club.id, boot(None, "Surfski", "Clubski").id, CLI)
    instellingen.opslaan("KV De Fuut", CLI)
    kaarten = kaartjes(ingelogd.get(f"/kaartjes/print?rek={club.rek_id}&rek={zonder.id}").text)
    soorten = {code: re.findall(r'kaartje-soorten">([^<]*)<', html) for code, html in kaarten.items()}
    assert soorten == {"A/1/1": ["Geschikt voor Kajak/Surfski"], "A/1/2": ["Geschikt voor Kajak"],
                       "A/1/3": ["Geschikt voor Surfski"], "A/1/4": ["Geschikt voor C11"],
                       "B/1/1": []}  # zonder bootsoort geen regel
    for html in kaarten.values():
        assert "vrij" not in html and "Anna de Vries" not in html and "kaartje-eigenaar" not in html
    # Zonder logo de naam van de vereniging bovenaan (BLB-027 criterium 3), en alleen daar.
    assert "<p>KV De Fuut</p>" in kaarten["A/1/1"] and "kaartje-logo" not in kaarten["A/1/1"]
    assert all(html.count("KV De Fuut") == 1 for html in kaarten.values())


def test_selectie_een_meerdere_per_rek_en_alle_in_volgorde_van_de_loods(ingelogd):  # noqa: F811
    vrij, bezet, _club, c11, _anna = loods()
    b1 = plaats("B/1/1")
    plaats("B/1/2")

    def codes(query):
        return list(kaartjes(ingelogd.get(f"/kaartjes/print?{query}").text))

    assert codes(f"plaats={c11.id}") == ["A/1/4"]
    assert codes(f"plaats={c11.id}&plaats={vrij.id}&plaats={b1.id}") == ["A/1/1", "A/1/4", "B/1/1"]
    assert codes(f"rek={b1.rek_id}") == ["B/1/1", "B/1/2"]
    assert codes(f"rek={b1.rek_id}&plaats={bezet.id}") == ["A/1/2", "B/1/1", "B/1/2"]
    assert codes("alle=1") == ["A/1/1", "A/1/2", "A/1/3", "A/1/4", "B/1/1", "B/1/2"]


def test_acht_kaartjes_per_blad(ingelogd):  # noqa: F811
    for i in range(9):
        plaats(f"A/{1 + i // 6}/{1 + i % 6}")
    tekst = ingelogd.get("/kaartjes/print?alle=1").text
    bladen = tekst.split('<div class="blad">')[1:]
    assert [b.count('class="kaartje"') for b in bladen] == [8, 1]


def test_hernoemen_houdt_de_qr_code_en_toont_de_nieuwe_code(ingelogd):  # noqa: F811
    p = plaats()
    oud = qr_pad(kaartjes(ingelogd.get(f"/kaartjes/print?plaats={p.id}").text)["A/1/1"])
    indeling.rek_wijzigen(p.rek_id, "Z", "", CLI)
    kaarten = kaartjes(ingelogd.get(f"/kaartjes/print?plaats={p.id}").text)
    assert list(kaarten) == ["Z/1/1"] and qr_pad(kaarten["Z/1/1"]) == oud


@pytest.mark.parametrize("query", ["", "plaats=999", "rek=999", "plaats=abc"])
def test_lege_of_onbekende_selectie_terug_met_melding(ingelogd, query):  # noqa: F811
    plaats()
    r = ingelogd.get(f"/kaartjes/print?{query}", follow_redirects=True)
    assert r.request.path == "/kaartjes"
    assert "Kies een of meer plaatsen, een rek of alle plaatsen." in r.text
    assert 'class="kaartje"' not in r.text


def test_kiezen_toont_rekken_plaatsen_en_alles(ingelogd):  # noqa: F811
    _vrij, bezet, _club, _c11, _anna = loods()
    tekst = ingelogd.get("/kaartjes").text
    assert 'name="alle"' in tekst and f'name="rek" value="{bezet.rek_id}"><label for="rek-{bezet.rek_id}">Heel A</label>' in tekst
    assert f'name="plaats" value="{bezet.id}"><label for="plaats-{bezet.id}">A/1/2</label>' in tekst
    assert "Anna de Vries" not in tekst


@pytest.mark.parametrize("pad", ["/kaartjes", "/kaartjes/print?alle=1"])
def test_kaartjes_vragen_inloggen(client, pad):
    plaats()
    r = client.get(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")
