"""Rekoverzicht (issue #87): welk plaatje en welke alt-tekst een vak krijgt, en de pagina."""

from pathlib import Path

import pytest

from app.domein import CLI, indeling, toewijzing
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.meet_plaatjes import contrast, meet, minimaal_contrast
from tests.unit.test_indeling_en_toewijzing import boot, soort
from tests.unit.test_web import inloggen

BOTEN = Path("app/web/static/boten")


def met_boot(code, soorten, bootsoort, club=False):
    p = plaats(code, [soort(s) for s in soorten], club)
    b = boot(None if club else lid().id, bootsoort)
    toewijzing.toewijzen(p.id, b.id, CLI)
    return p


def test_bezet_toont_de_soort_van_de_boot_niet_van_de_plaats(app):
    # Mutant: p.bootsoorten[0] in plaats van p.boot.bootsoort valt op bestand (kajak-bezet.jpg);
    # `bezet` altijd False valt op de toestand.
    p = met_boot("A/1/1", ["Kajak", "Canadese kano"], "Canadese kano")
    assert indeling.plaatje(p) == {
        "plaats_id": p.id, "bestand": "canadese-kano-bezet.jpg", "bezet": True, "tekst": "", "club": False,
        "titel": "A/1/1 - Canadese kano: Zeemeeuw (Anna de Vries)",
        "alt": "Plaats A/1/1, Canadese kano, bezet"}


def test_vrij_toont_de_eerste_soort_en_de_alt_noemt_alle_soorten(app):
    # De volgorde is die van de bootsoorten (id). Mutant: de laatste soort nemen valt op bestand;
    # alleen de eerste noemen valt op alt.
    v = indeling.plaatje(plaats("A/1/1", [soort("Surfski"), soort("Kajak")]))
    assert v["bestand"] == "kajak-vrij.jpg" and not v["club"] and not v["bezet"]
    assert v["alt"] == "Plaats A/1/1, Kajak, Surfski, vrij"
    assert v["titel"] == "A/1/1 - Kajak, Surfski: vrij"


def test_lege_clubplaats_is_vrij_met_stippelrand(app):
    # Mutant: club alleen op is_clubplaats (zonder `and not p.boot`) valt in het volgende geval.
    v = indeling.plaatje(plaats("A/1/1", [soort("Kajak")], club=True))
    assert v["bestand"] == "kajak-vrij.jpg" and v["club"] and not v["bezet"]
    assert v["alt"] == "Plaats A/1/1, Kajak, clubplaats, leeg"
    assert v["titel"] == "A/1/1 - Kajak: clubplaats, leeg"


def test_clubplaats_met_clubboot_is_bezet_zonder_stippelrand(app):
    v = indeling.plaatje(met_boot("A/1/1", ["Kajak"], "Kajak", club=True))
    assert v["bestand"] == "kajak-bezet.jpg" and not v["club"] and v["bezet"]
    assert v["alt"] == "Plaats A/1/1, Kajak, clubplaats, bezet"
    assert v["titel"] == "A/1/1 - Kajak: Zeemeeuw (clubboot)"


def test_plaats_zonder_bootsoort_is_een_leeg_vak(app):
    v = indeling.plaatje(indeling.rek_aanmaken("A", "", {(1, 1)}, CLI).plaatsen[0])
    assert v["bestand"] is None and v["tekst"] == ""
    assert v["alt"] == "Plaats A/1/1, geen bootsoort, vrij"
    assert v["titel"] == "A/1/1 - geen bootsoort: vrij"


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
    p = plaats("A/2/1")
    plaats("A/1/1")
    assert indeling.rekoverzicht(p.rek).keys() == {(1, 1), (2, 1)}


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def test_pagina_vraagt_inloggen(client):
    r = client.get("/rekoverzicht")
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_menu_item_rekoverzicht(ingelogd):
    assert '<a class="dj-nav__link" href="/rekoverzicht">Rekoverzicht</a>' in ingelogd.get("/").text


def test_pagina_toont_per_plaats_een_plaatje_met_alt(ingelogd):
    p = met_boot("A/1/1", ["Kajak"], "Kajak")
    vrij = plaats("A/1/2", [soort("Supboard")])
    tekst = ingelogd.get("/rekoverzicht").text
    assert f'href="/plaatsen/{p.id}"' in tekst
    assert 'src="/static/boten/kajak-bezet.jpg" alt="Plaats A/1/1, Kajak, bezet"' in tekst
    assert '<a class="bl-vak" title="A/1/1' in tekst, "een cel met plaatje is niet bezet gestijld"
    assert 'title="A/1/1 - Kajak: Zeemeeuw (Anna de Vries)"' in tekst, "tekstballon, bezet"
    assert 'title="A/1/2 - Supboard: vrij"' in tekst, "tekstballon bij een vrije plaats"
    assert f'href="/plaatsen/{vrij.id}"' in tekst
    assert "Plaats A/1/2, Supboard, vrij</span>" in tekst
    assert '<a class="bl-vak" title="A/1/2' in tekst, "vrij zonder plaatje: omrand, niet gevuld"


def test_cel_zonder_plaatje_is_gevuld_als_hij_bezet_is(ingelogd):
    # Mutant: bl-vak--bezet altijd zetten valt op de vrije cel; nooit zetten valt op de bezette.
    met_boot("A/1/1", ["Supboard"], "Supboard")
    plaats("A/1/2", [soort("Supboard")])
    tekst = ingelogd.get("/rekoverzicht").text
    assert '<a class="bl-vak bl-vak--bezet" title="A/1/1 - Supboard: Zeemeeuw (Anna de Vries)"' in tekst
    assert '<span class="bl-vak__tekst" aria-hidden="true">Supboard</span>' in tekst
    assert tekst.count("bl-vak--bezet") == 1


def test_pagina_toont_de_naam_van_een_soort_zonder_plaatje_geescaped(ingelogd):
    # Issue #88: de zichtbare tekst ({{ v.tekst }}) en de alt-tekst, met < en " in de naam.
    s = indeling.bootsoort_toevoegen('Sup <"xl">', CLI)
    plaats("A/1/1", [s.id])
    tekst = ingelogd.get("/rekoverzicht").text
    assert '<span class="bl-vak__tekst" aria-hidden="true">Sup &lt;&#34;xl&#34;&gt;</span>' in tekst
    assert "Plaats A/1/1, Sup &lt;&#34;xl&#34;&gt;, vrij</span>" in tekst
    assert 'title="A/1/1 - Sup &lt;&#34;xl&#34;&gt;: vrij"' in tekst, "tekstballon (issue #95)"
    assert 'Sup <"xl">' not in tekst


def test_pagina_zet_verdieping_1_onderaan(ingelogd):
    plaats("A/1/1")
    plaats("A/2/1")
    tekst = ingelogd.get("/rekoverzicht").text
    assert tekst.index("Verdieping 2") < tekst.index("Verdieping 1"), "verdieping 1 hoort onderaan"


def test_pagina_toont_verdiepingen_tot_de_hoogste_met_een_plaats(ingelogd):
    # Issues #89 en #94: plaatsen op verdieping 1 en 3; verdieping 2 blijft staan, 4 en 5 niet.
    plaats("A/1/1")
    plaats("A/3/1")
    tekst = ingelogd.get("/rekoverzicht").text
    rijen = [f"Verdieping {v}</span>" for v in (3, 2, 1)]
    assert sorted(rijen, key=tekst.index) == rijen, "verdieping 1 onderaan"
    assert tekst.count('class="bl-rek__label"') == 3
    assert "Verdieping 4" not in tekst and "Verdieping 5" not in tekst


def test_pagina_toont_zoveel_kolommen_als_het_hoogste_vak_van_dat_rek(ingelogd):
    indeling.rek_aanmaken("A", "", {(1, k) for k in range(1, 7)} | {(2, 1)}, CLI)
    indeling.rek_aanmaken("B", "", {(1, k) for k in range(1, 13)}, CLI)
    secties = ingelogd.get("/rekoverzicht").text.split("<section")[1:]
    assert [s.count('class="bl-rek__nr"') for s in secties] == [6, 12]
    assert [s.count('class="bl-rek__label"') for s in secties] == [2, 1]
    # Een lege cel houdt de kolommen op hun plaats: de kopregel heeft een lege cel, rij 2 van rek A vijf.
    assert [s.count("<span></span>") for s in secties] == [1 + 5, 1 + 0]


def test_rekoverzicht_escapet_naam_en_omschrijving_van_het_rek(ingelogd):
    # Mutant: |safe op rek.naam of rek.omschrijving valt hier.
    indeling.rek_aanmaken("<b>x<b>", "<i>y</i>", {(1, 1)}, CLI)
    tekst = ingelogd.get("/rekoverzicht").text
    assert "&lt;b&gt;x&lt;b&gt;" in tekst and "&lt;i&gt;y&lt;/i&gt;" in tekst
    assert "<b>x<b>" not in tekst and "<i>y</i>" not in tekst


def test_vrije_plaatjes_halen_3_op_1_en_zijn_ook_in_grijs_te_onderscheiden():
    # Issue #155. Mutant: de oude plaatjes (rand 2,0:1, geen dikke lijn) of een lijn van 3 px (1,3 px
    # op 56 px) valt op rand of dikte; gelijke kleur voor bezet en vrij valt op het grijsverschil.
    for basis in sorted(set(indeling.PLAATJES.values())):
        vrij, bezet = meet(BOTEN / f"{basis}-vrij.jpg"), meet(BOTEN / f"{basis}-bezet.jpg")
        assert vrij["rand"] >= 3 and vrij["dikte"] >= 2, (basis, vrij)
        assert minimaal_contrast(bezet["midden"]) >= 3, (basis, bezet)
        assert contrast(bezet["midden"], vrij["midden"]) >= 3, basis
