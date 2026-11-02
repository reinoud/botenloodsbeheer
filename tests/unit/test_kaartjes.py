"""Kaartjes met QR-code (BLB-021, BLB-027 criteria 1 en 2 deel kaartjes, ADR-011, ADR-003)."""

import re

import pytest
import segno

from app.domein import CLI, indeling, instellingen, toewijzing
from tests.unit.hulp import png
from tests.unit.test_indeling_en_toewijzing import boot, plaats
from tests.unit.test_overzichten_en_instellingen import logo_uit_installatie, loods
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


def test_kaartje_met_logo_code_eigenaar_en_qr_naar_openbare_pagina(app, ingelogd, tmp_path):  # noqa: F811
    kenmerk, _ = logo_uit_installatie(app, tmp_path, png())
    _vrij, bezet, _club, _c11, _anna = loods()
    r = ingelogd.get(f"/kaartjes/print?plaats={bezet.id}")
    assert r.status_code == 200
    kaart = kaartjes(r.text)["A02"]
    assert f'src="/logo/{kenmerk}"' in kaart and ">A02<" in kaart and "Anna de Vries" in kaart
    assert qr_pad(kaart) == qr_van(f"http://localhost:8080/p/{bezet.publieke_sleutel}")
    # Geen adres, telefoon, e-mail, lidnummer of boot (overlay §8); de QR-code zelf zonder tekst.
    for verboden in ("Proefweg", "06-0000", "@example.org", "1001", "Zeemeeuw"):
        assert verboden not in r.text
    assert "<title" not in kaart.split("<svg", 1)[1]


def test_vrije_plaats_en_clubplaats(ingelogd):  # noqa: F811
    _vrij, _bezet, club, _c11, _anna = loods()
    lege_club = plaats("A05", club=True, rek=club.rek)
    toewijzing.toewijzen(club.id, boot(None, "Surfski", "Clubski").id, CLI)
    instellingen.opslaan("KV De Fuut", "#1a4d2e", "#333333", CLI)
    kaarten = kaartjes(ingelogd.get(f"/kaartjes/print?rek={club.rek_id}").text)
    eigenaren = {code: re.search(r'kaartje-eigenaar">([^<]*)<', html).group(1)
                 for code, html in kaarten.items()}
    assert eigenaren == {"A01": "vrij", "A02": "Anna de Vries", "A03": "KV De Fuut",
                         "A04": "vrij", lege_club.code: "KV De Fuut"}
    # Zonder logo de naam van de vereniging bovenaan (BLB-027 criterium 3).
    assert "<p>KV De Fuut</p>" in kaarten["A01"] and "kaartje-logo" not in kaarten["A01"]


def test_selectie_een_meerdere_per_rek_en_alle_in_volgorde_van_de_loods(ingelogd):  # noqa: F811
    vrij, bezet, _club, c11, _anna = loods()
    b1 = plaats("B01", rek=indeling.rek_aanmaken("Rek B", CLI))
    plaats("B02", rek=b1.rek)

    def codes(query):
        return list(kaartjes(ingelogd.get(f"/kaartjes/print?{query}").text))

    assert codes(f"plaats={c11.id}") == ["A04"]
    assert codes(f"plaats={c11.id}&plaats={vrij.id}&plaats={b1.id}") == ["A01", "A04", "B01"]
    assert codes(f"rek={b1.rek_id}") == ["B01", "B02"]
    assert codes(f"rek={b1.rek_id}&plaats={bezet.id}") == ["A02", "B01", "B02"]
    assert codes("alle=1") == ["A01", "A02", "A03", "A04", "B01", "B02"]


def test_acht_kaartjes_per_blad(ingelogd):  # noqa: F811
    rek = indeling.rek_aanmaken("Rek A", CLI)
    for i in range(9):
        plaats(f"A{i:02}", rek=rek)
    tekst = ingelogd.get("/kaartjes/print?alle=1").text
    bladen = tekst.split('<div class="blad">')[1:]
    assert [b.count('class="kaartje"') for b in bladen] == [8, 1]


def test_hernoemen_houdt_de_qr_code_en_toont_de_nieuwe_code(ingelogd):  # noqa: F811
    p = plaats()
    oud = qr_pad(kaartjes(ingelogd.get(f"/kaartjes/print?plaats={p.id}").text)["A01"])
    indeling.plaats_wijzigen(p.id, "Z99", [1], False, CLI)
    kaarten = kaartjes(ingelogd.get(f"/kaartjes/print?plaats={p.id}").text)
    assert list(kaarten) == ["Z99"] and qr_pad(kaarten["Z99"]) == oud


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
    assert 'name="alle"' in tekst and f'name="rek" value="{bezet.rek_id}"> Heel Rek A' in tekst
    assert f'name="plaats" value="{bezet.id}"> A02' in tekst
    assert "Anna de Vries" not in tekst


@pytest.mark.parametrize("pad", ["/kaartjes", "/kaartjes/print?alle=1"])
def test_kaartjes_vragen_inloggen(client, pad):
    plaats()
    r = client.get(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")
