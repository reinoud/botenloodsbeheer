"""Beheerschermen en openbare pagina via de Flask-testclient (BLB-001, 005, 010, 012, 020, 025)."""

import io

import pytest
from sqlalchemy import select

from app.domein import CLI, boten, indeling, log, toewijzing
from app.models import Plaats, Rek, db
from app.web import getal
from tests.unit.hulp import beheerder_met_wachtwoord, lid, png
from tests.unit.test_web import inloggen

BEHEER = ["/indeling", "/boten", "/leden", "/plaatsen/1", "/boten/1", "/beheerders",
          "/profiel", "/log", "/log/techniek"]


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def bezette_plaats(club=False, foto=None):
    rek = indeling.rek_aanmaken("Rek A", CLI)
    p = indeling.plaats_aanmaken(rek.id, "A01", [1], club, CLI)
    eigenaar = None if club else lid().id
    b = boten.boot_aanmaken("Zeemeeuw", 1, eigenaar, foto, CLI)
    toewijzing.toewijzen(p.id, b.id, CLI)
    return p


@pytest.mark.parametrize("pad", BEHEER)
def test_beheer_vraagt_inloggen(client, pad):
    r = client.get(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")


@pytest.mark.parametrize("pad", ["/rekken", "/rekken/1/plaatsen", "/plaatsen/1/toewijzen",
                                 "/boten", "/leden/ophalen", "/rekken/1/verwijderen",
                                 "/plaatsen/1", "/plaatsen/1/vrijgeven", "/boten/1"])
def test_bezoeker_kan_niets_wijzigen(client, pad):
    r = client.post(pad, data={"naam": "Rek X", "code": "X1", "bootsoort": 1})
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.scalar(select(Rek)) is None


def test_indeling_aanmaken_en_dubbele_code(ingelogd):
    ingelogd.post("/rekken", data={"naam": "Rek A"})
    rek = db.session.scalar(select(Rek))
    ingelogd.post(f"/rekken/{rek.id}/plaatsen", data={"code": "A01", "bootsoort": ["1", "3"]})
    r = ingelogd.post(f"/rekken/{rek.id}/plaatsen", data={"code": "A01", "bootsoort": "1"},
                      follow_redirects=True)
    assert "De code A01 hoort al bij een andere plaats." in r.text
    p = db.session.scalar(select(Plaats))
    assert [s.naam for s in p.bootsoorten] == ["Kajak", "Surfski"]
    # BLB-043: onder /indeling geen log; de indeling staat in het technische log.
    assert 'class="log"' not in r.text
    techniek = ingelogd.get("/log/techniek").text
    assert "rek.aangemaakt" in techniek and "plaats.aangemaakt" in techniek


def test_boot_vastleggen_met_ongeldige_foto(ingelogd):
    anna = lid()
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": str(anna.id),
                                      "foto": (io.BytesIO(b"tekst"), "boot.jpg")},
                      follow_redirects=True)
    assert "geen geldige afbeelding" in r.text and anna.boten == []
    r = ingelogd.post("/boten", data={"naam": "Clubkajak", "bootsoort": "1", "eigenaar": "club"},
                      follow_redirects=True)
    assert "De boot is vastgelegd." in r.text and "boot.aangemaakt" in r.text


def test_plaatsdetail_met_eigenaar_en_log(ingelogd):
    p = bezette_plaats()
    tekst = ingelogd.get(f"/plaatsen/{p.id}").text
    for waarde in ("Zeemeeuw", "Anna de Vries", "1001", "Proefweg 1", "06-00001234",
                   "1001@example.org", "plaats.toegewezen", f"/p/{p.publieke_sleutel}"):
        assert waarde in tekst


def test_plaatsdetail_clubboot_zonder_persoonsgegevens(ingelogd):
    p = bezette_plaats(club=True)
    tekst = ingelogd.get(f"/plaatsen/{p.id}").text
    assert "(clubboot)" in tekst and "Lidnummer" not in tekst and "@example.org" not in tekst


def test_plaatsdetail_vrij_met_geschikte_soorten(ingelogd):
    rek = indeling.rek_aanmaken("Rek A", CLI)
    p = indeling.plaats_aanmaken(rek.id, "A01", [1, 4], False, CLI)
    tekst = ingelogd.get(f"/plaatsen/{p.id}").text
    assert "Deze plaats is vrij" in tekst and "Kajak, C11" in tekst


def test_toewijzen_geweigerd_toont_reden(ingelogd):
    rek = indeling.rek_aanmaken("Rek A", CLI)
    p = indeling.plaats_aanmaken(rek.id, "A01", [1], False, CLI)
    b = boten.boot_aanmaken("Clubkajak", 1, None, None, CLI)
    r = ingelogd.post(f"/plaatsen/{p.id}/toewijzen", data={"boot_id": b.id}, follow_redirects=True)
    assert "is een clubboot en hoort op een clubplaats" in r.text


def test_import_aanvragen(ingelogd):
    """BLB-006 criterium 5, deel webinterface: het verzoek staat op de pagina en in het log."""
    r = ingelogd.post("/leden/ophalen", follow_redirects=True)
    assert "De import is aangevraagd" in r.text and "aangevraagd" in r.text
    r = ingelogd.post("/leden/ophalen", follow_redirects=True)
    assert "Er staat al een import klaar." in r.text
    assert "leden.import_aangevraagd" not in r.text  # technisch: niet onder het overzicht
    assert "leden.import_aangevraagd" in ingelogd.get("/log/techniek").text


def test_openbare_pagina_alleen_openbare_gegevens(client):
    p = bezette_plaats(foto=png())
    r = client.get(f"/p/{p.publieke_sleutel}")
    assert r.status_code == 200
    assert "A01" in r.text and "Zeemeeuw" in r.text and "Anna de Vries" in r.text
    assert "/afbeelding/" in r.text
    for verboden in ("Proefweg", "06-0000", "@example.org", "1001", "Log", "plaats.toegewezen"):
        assert verboden not in r.text


def test_openbare_pagina_zet_geen_sessiecookie(client):
    p = bezette_plaats()
    for pad in (f"/p/{p.publieke_sleutel}", "/p/bestaatniet"):
        r = client.get(pad)
        assert "Set-Cookie" not in r.headers and 'name="csrf-token"' not in r.text
    assert "Set-Cookie" in client.get("/inloggen").headers  # elders wel, voor het csrf-token


def test_openbare_pagina_clubboot_en_onbekend(client):
    p = bezette_plaats(club=True)
    assert "Botenloods" in client.get(f"/p/{p.publieke_sleutel}").text
    r = client.get("/p/bestaatniet")
    assert r.status_code == 404 and "Deze pagina bestaat niet" in r.text
    assert client.get(f"/p/{p.code}").status_code == 404
    assert client.get(f"/p/{p.id}").status_code == 404


def test_afbeelding_met_headers(client):
    p = bezette_plaats(foto=png())
    sleutel = indeling.openbaar(p.publieke_sleutel)["foto"]
    r = client.get(f"/afbeelding/{sleutel}")
    assert r.status_code == 200 and r.mimetype == "image/jpeg"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Content-Disposition"] == "inline"
    assert "immutable" in r.headers["Cache-Control"]
    assert client.get("/afbeelding/onbekend").status_code == 404


def test_upload_boven_grens_geweigerd(ingelogd, app):
    groot = b"x" * (app.config["MAX_CONTENT_LENGTH"] + 1)
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": "club",
                                      "foto": (io.BytesIO(groot), "groot.jpg")})
    assert r.status_code == 413


def test_plaats_wijzigen_en_vrijgeven(ingelogd):
    p = bezette_plaats()
    sleutel = p.publieke_sleutel
    r = ingelogd.post(f"/plaatsen/{p.id}", data={"code": "A01", "bootsoort": "3"},
                      follow_redirects=True)
    assert "Op plaats A01 ligt Zeemeeuw, een kajak" in r.text
    r = ingelogd.post(f"/plaatsen/{p.id}", data={"code": "B09", "bootsoort": ["1", "3"]},
                      follow_redirects=True)
    assert "De plaats is opgeslagen." in r.text and "plaats.gewijzigd" not in r.text
    assert "plaats.gewijzigd" in ingelogd.get("/log/techniek").text
    assert "Plaats B09" in ingelogd.get(f"/p/{sleutel}").text
    r = ingelogd.post(f"/plaatsen/{p.id}/vrijgeven", follow_redirects=True)
    assert "De plaats is vrijgegeven." in r.text and "Deze plaats is vrij" in r.text
    assert "plaats.vrijgegeven" in r.text
    assert db.session.get(Plaats, p.id).boot_id is None


def test_twee_logs_gescheiden(ingelogd):
    """BLB-043: een toewijzing staat alleen bij de bootmutaties, de indeling alleen technisch;
    onder plaats, boot en lid alleen bootmutaties."""
    p = bezette_plaats()
    boot, lid_id = p.boot.id, p.boot.lid_id
    mutaties, techniek = ingelogd.get("/log").text, ingelogd.get("/log/techniek").text
    assert "plaats.toegewezen" in mutaties and "plaats.aangemaakt" not in mutaties
    assert "plaats.aangemaakt" in techniek and "plaats.toegewezen" not in techniek
    for pad in (f"/plaatsen/{p.id}", f"/boten/{boot}", f"/leden/{lid_id}"):
        tekst = ingelogd.get(pad).text
        assert "plaats.toegewezen" in tekst and "plaats.aangemaakt" not in tekst, pad
    assert "beheerder." not in ingelogd.get("/").text


def _bootmutaties(aantal):
    for _ in range(aantal):
        log.schrijf(CLI, "boot.aangemaakt", ["boot:1"])
    db.session.commit()


def test_log_bladert_per_50_regels(ingelogd):
    _bootmutaties(51)
    eerste = ingelogd.get("/log").text
    assert eerste.count("<td data-label=\"Actie\">") == 50
    assert "pagina=2" in eerste and "Nieuwere regels" not in eerste
    tweede = ingelogd.get("/log?pagina=2").text
    assert tweede.count("<td data-label=\"Actie\">") == 1
    assert "Nieuwere regels" in tweede and "Oudere regels" not in tweede
    assert "Meer in het log" not in eerste
    assert "Meer in het log" in ingelogd.get("/boten").text


def test_overzicht_met_49_regels_heeft_geen_link_naar_het_log(ingelogd):
    _bootmutaties(49)
    assert "Meer in het log" not in ingelogd.get("/boten").text


def test_log_met_precies_50_regels_heeft_geen_volgende_pagina(ingelogd):
    _bootmutaties(50)
    tekst = ingelogd.get("/log").text
    assert "Oudere regels" not in tekst and "Nieuwere regels" not in tekst


@pytest.mark.parametrize("pagina", ["abc", "0", "-3", "1" + "0" * 30])
def test_ongeldige_pagina_geeft_geen_fout(ingelogd, pagina):
    assert ingelogd.get(f"/log/techniek?pagina={pagina}").status_code == 200


def test_boot_wijzigen_via_het_formulier_en_log_op_alle_plaatsen(ingelogd):
    anna, bert = lid(), lid("1002", "Bert Jansen")
    b = boten.boot_aanmaken("Zeemeeuw", 1, anna.id, None, CLI)
    form = ingelogd.get(f"/boten/{b.id}").text
    assert 'value="Zeemeeuw"' in form and "Boot opslaan" in form
    r = ingelogd.post(f"/boten/{b.id}", data={"naam": "Fuut", "bootsoort": "3", "eigenaar": str(bert.id)},
                      follow_redirects=True)
    assert "De boot is opgeslagen." in r.text and "Fuut" in r.text and "boot.gewijzigd" in r.text
    for pad in (f"/boten/{b.id}", f"/leden/{anna.id}", f"/leden/{bert.id}", "/boten", "/log"):
        assert "boot.gewijzigd" in ingelogd.get(pad).text, pad
    assert "boot.gewijzigd" not in ingelogd.get("/log/techniek").text
    assert anna.email not in r.text


def test_boot_wijzigen_weigeringen_via_het_formulier(ingelogd):
    p = bezette_plaats()  # kajak van een lid op een plaats voor kajaks
    boot_id = p.boot_id
    r = ingelogd.post(f"/boten/{boot_id}", data={"naam": "Zeemeeuw", "bootsoort": "4", "eigenaar": "club"},
                      follow_redirects=True)
    assert "is een clubboot en hoort op een clubplaats" in r.text and "De boot is opgeslagen." not in r.text
    r = ingelogd.post(f"/boten/{boot_id}", data={"naam": "Zeemeeuw", "bootsoort": "4",
                                                   "eigenaar": str(p.boot.lid_id)}, follow_redirects=True)
    assert "niet geschikt voor een c11" in r.text
    r = ingelogd.post(f"/boten/{boot_id}", data={"naam": "Zeemeeuw", "bootsoort": "1"}, follow_redirects=True)
    assert "Kies een eigenaar." in r.text
    assert ingelogd.post("/boten/999", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": "club"}).status_code == 404


# Id buiten het bereik van integer en een NUL-teken (#67). Met TESTING komt een onafgevangen fout
# als exceptie in de test, dus geen exceptie betekent ook geen ERROR-regel in de log.
@pytest.mark.parametrize("pad,status", [
    ("/boten/2147483647", 404), ("/boten/2147483648", 404), ("/plaatsen/99999999999", 404),
    ("/leden/2147483648", 404), ("/leden?zoek=%00", 400), ("/leden?zoek=Jansen", 200),
    ("/p/%00", 400), ("/afbeelding/%00", 400),
], ids=["grens_binnen", "grens_buiten", "plaats", "lid", "zoek_nul", "zoek_gewoon", "p_nul",
        "afbeelding_nul"])
def test_te_groot_id_of_nul_teken_geeft_geen_500(ingelogd, pad, status):
    assert ingelogd.get(pad).status_code == status


@pytest.mark.parametrize("waarde,goed", [
    ("2147483647", True), ("-2147483648", True), ("2147483648", False), ("-2147483649", False),
], ids=["max_binnen", "min_binnen", "max_buiten", "min_buiten"])
def test_getal_binnen_integer_van_postgresql(waarde, goed):
    """#74: buiten de grens een ValueError, zodat Werkzeug de standaardwaarde geeft."""
    if goed:
        assert getal(waarde) == int(waarde)
    else:
        with pytest.raises(ValueError):
            getal(waarde)


# Te groot getal in querystring of formulier (#74): een gewone melding, geen DataError (500).
# 2147483647 komt wel bij de database en geeft daar "bestaat niet".
@pytest.mark.parametrize("eigenaar,melding", [
    ("2147483647", "Dit lid bestaat niet."), ("2147483648", "Kies een eigenaar."),
], ids=["eigenaar_binnen", "eigenaar_buiten"])
def test_te_groot_getal_in_formulier_geeft_melding(ingelogd, eigenaar, melding):
    p = bezette_plaats()
    r = ingelogd.post(f"/boten/{p.boot_id}", data={"naam": "Fuut", "bootsoort": "1",
                                                   "eigenaar": eigenaar}, follow_redirects=True)
    assert melding in r.text


def test_te_groot_getal_bij_toewijzen_bootsoort_en_overzicht(ingelogd):
    p = bezette_plaats()
    groot = "2147483648"
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": groot, "eigenaar": "club"},
                      follow_redirects=True)
    assert "Kies een bootsoort." in r.text
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": groot},
                      follow_redirects=True)
    assert "Kies een eigenaar." in r.text
    r = ingelogd.post(f"/boten/{p.boot_id}", data={"naam": "Fuut", "bootsoort": groot,
                                                   "eigenaar": "club"}, follow_redirects=True)
    assert "Kies een bootsoort." in r.text
    assert ingelogd.post(f"/plaatsen/{p.id}", data={"code": "A01", "bootsoort": groot}).status_code == 302
    assert ingelogd.post(f"/plaatsen/{p.id}/toewijzen", data={"boot_id": groot}).status_code == 302
    assert ingelogd.post(f"/rekken/{p.rek_id}/plaatsen",
                         data={"code": "A02", "bootsoort": groot}).status_code == 302
    assert ingelogd.get(f"/vrij?bootsoort={groot}").status_code == 200


def test_nul_teken_in_formulier_geeft_400(ingelogd):
    p = bezette_plaats()
    r = ingelogd.post(f"/boten/{p.boot_id}", data={"naam": "Zee\x00meeuw", "bootsoort": "1",
                                                   "eigenaar": "club"})
    assert r.status_code == 400
