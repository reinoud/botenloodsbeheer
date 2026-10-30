"""Beheerschermen en openbare pagina via de Flask-testclient (BLB-001, 005, 010, 012, 020, 025)."""

import io

import pytest
from sqlalchemy import select

from app.domein import CLI, boten, indeling, toewijzing
from app.models import Plaats, Rek, db
from tests.unit.hulp import beheerder_met_wachtwoord, lid, png
from tests.unit.test_web import inloggen

BEHEER = ["/indeling", "/boten", "/leden", "/plaatsen/1", "/boten/1"]


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
                                 "/boten", "/leden/ophalen", "/rekken/1/verwijderen"])
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
    assert "rek.aangemaakt" in r.text and "plaats.aangemaakt" in r.text  # log onder het scherm


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


def test_synchronisatie_aanvragen(ingelogd):
    r = ingelogd.post("/leden/ophalen", follow_redirects=True)
    assert "De synchronisatie is aangevraagd" in r.text and "aangevraagd" in r.text


def test_openbare_pagina_alleen_openbare_gegevens(client):
    p = bezette_plaats(foto=png())
    r = client.get(f"/p/{p.publieke_sleutel}")
    assert r.status_code == 200
    assert "A01" in r.text and "Zeemeeuw" in r.text and "Anna de Vries" in r.text
    assert "/afbeelding/" in r.text
    for verboden in ("Proefweg", "06-0000", "@example.org", "1001", "Log", "plaats.toegewezen"):
        assert verboden not in r.text


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
