"""Foutpagina 403 en 404 in de webinterface (BV-95, issue #341): huisstijl, juiste statuscode, een link terug
per situatie, en de sessie wordt gelezen zoals laad_beheerder dat doet. De API houdt zijn JSON-fout
(test_leesaanroepen.py::test_onbekend_pad_en_verkeerde_methode_geven_json)."""

import re

import pytest

from app.domein import CLI, instellingen
from tests.unit.test_kijkers import als_kijker, beheerder, main  # noqa: F401

KOP = {403: "Geen toegang", 404: "Pagina niet gevonden"}


def pagina(r, code, terug_naar, kop_met_menu):
    """Toetst de gedeelde onderdelen: statuscode, data-fout, kop, regel Foutcode, één knop naar terug_naar,
    en menu en zoekveld alleen als kop_met_menu."""
    assert r.status_code == code
    tekst = r.text
    assert re.search(rf'<main [^>]*data-fout="{code}"', tekst), "geen foutpagina in de huisstijl"
    assert re.search(rf"<h1>{KOP[code]}</h1>", tekst)
    assert f"Foutcode {code}" in tekst
    assert re.findall(r'<a class="ds-btn ds-btn--primary" href="([^"]+)"', tekst) == [terug_naar]
    assert ('role="search"' in tekst) is kop_met_menu
    assert ('class="dj-menu"' in tekst) is kop_met_menu
    assert "Werkzeug" not in tekst and "requested URL" not in tekst
    assert "aria-current" not in tekst.split("<main")[0]  # geen pagina gemarkeerd (BV-95)
    assert r.headers["Cache-Control"] == "no-store"


def test_beheerder_krijgt_404_met_menu_en_link_naar_het_rekoverzicht(beheerder):  # noqa: F811
    r = beheerder.get("/bestaatniet")
    pagina(r, 404, "/rekoverzicht", True)
    assert 'aria-label="Hoofdmenu"' in r.text and ">Technisch log<" in r.text  # menu met vier groepen


def test_kijker_krijgt_403_met_menu_2b_zonder_de_pagina_te_verraden(app):
    kijker, _ = als_kijker(app)
    r = kijker.get("/log")
    pagina(r, 403, "/rekoverzicht", True)
    assert ">Technisch log<" not in r.text and ">Gebruikers<" not in r.text  # menu 2B
    assert ">Vrije plaatsen<" in r.text
    assert "Met je account kun je deze pagina niet openen." in r.text
    assert "log" not in main(r.text).lower().replace("foutcode", "")  # noemt de pagina niet


def test_kijker_krijgt_404_met_menu_2b(app):
    kijker, _ = als_kijker(app)
    r = kijker.get("/bestaatniet")
    pagina(r, 404, "/rekoverzicht", True)
    assert ">Gebruikers<" not in r.text and ">Boten<" in r.text


def test_uitgelogd_404_heeft_alleen_het_logo_en_een_link_naar_inloggen(client):
    r = client.get("/bestaatniet")
    pagina(r, 404, "/inloggen", False)
    assert '<a class="dj-logo" href="/inloggen">' in r.text
    assert "csrf-token" not in r.text and "Set-Cookie" not in r.headers  # geen sessiecookie (#9)


def test_beheerder_403_komt_niet_voor_en_uitgelogd_403_toont_de_403_tekst(app, client):
    # Geen eigen variant (besluit 3): dezelfde pagina als uitgelogd, met de 403-tekst.
    from flask import abort

    @app.get("/alleen-voor-de-proef")
    def proef():
        abort(403)

    pagina(client.get("/alleen-voor-de-proef"), 403, "/inloggen", False)


@pytest.mark.parametrize("pad", ["/boten/999999", "/leden/999999"])
def test_beheerder_404_binnen_een_route_markeert_geen_menu_item(beheerder, pad):  # noqa: F811
    # abort(404) in de route: request.endpoint is gezet, toch geen Boten of Leden gemarkeerd (toets #341).
    pagina(beheerder.get(pad), 404, "/rekoverzicht", True)


def test_kijker_404_op_een_onbekende_boot_markeert_boten_niet(app):
    kijker, _ = als_kijker(app)
    pagina(kijker.get("/boten/999999"), 404, "/rekoverzicht", True)


def test_verlopen_sessie_toont_de_uitgelogde_variant(beheerder):  # noqa: F811
    with beheerder.session_transaction() as s:
        s["sessieversie"] = -1
    pagina(beheerder.get("/bestaatniet"), 404, "/inloggen", False)


def test_vereniging_in_de_titel_wordt_geescaped(app, client):
    instellingen.opslaan("<b>x</b>", CLI)
    tekst = client.get("/bestaatniet").text
    assert "<title>Pagina niet gevonden · &lt;b&gt;x&lt;/b&gt;</title>" in tekst and "<b>x</b>" not in tekst


@pytest.mark.parametrize("pad", ["/p/bestaatniet", "/afbeelding/bestaatniet", "/logo/0123456789abcdef"])
def test_routes_met_een_eigen_404_blijven_zoals_ze_waren(client, pad):
    r = client.get(pad)
    assert r.status_code == 404
    assert ("Deze pagina bestaat niet" in r.text) is pad.startswith("/p/")
    assert ("Foutcode" in r.text) is False
