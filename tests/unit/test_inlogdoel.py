"""Na het inloggen terug naar de pagina die je opende (#354): de controle van het doel, het doel per
inlogroute en de herkomst van het doel (GET, Referer, recente inlog)."""

import time
from urllib.parse import parse_qs, urlsplit

import pytest

from app.domein import beheerders
from app.web import veilig_doel
from tests.unit.hulp import WACHTWOORD, beheerder_met_wachtwoord, code_bij

VAST = {"gebruikersnaam": "anna", "wachtwoord": WACHTWOORD}


@pytest.mark.parametrize("doel", [
    "https://andere.site", "//andere.site", "/\\andere.site", "javascript:alert(1)", "andere.site", "",
    None, "/log\rLocation: x", "/log\nx", "/log\tx", "/log\x00", "/log\x7f", "/%0d%0aX", "/log%09x", "/%2f",
    "/%2fandere.site", "/%5candere.site", "/a\\b", "/" + "a" * 1000,
], ids=["https", "dubbele_slash", "backslash_na_slash", "javascript", "zonder_slash", "leeg", "geen_tekst",
        "cr", "lf", "tab", "nul", "del", "gecodeerd_crlf", "gecodeerde_tab", "gecodeerde_slash",
        "gecodeerde_host", "gecodeerde_backslash", "backslash_midden", "te_lang"])
def test_veilig_doel_weigert(doel):
    assert veilig_doel(doel) is None


@pytest.mark.parametrize("doel", ["/", "/boten/12", "/boten/12?q=a%2Fb&x=1", "/zoeken?q=a b"])
def test_veilig_doel_laat_een_pad_binnen_de_applicatie_door(doel):
    assert veilig_doel(doel) == doel


def doel_van(url):
    """Het doel in de querystring van een inlog-URL, gedecodeerd; None zonder doel."""
    return parse_qs(urlsplit(url).query).get("volgende", [None])[0]


def code_stap(client, geheim, volgende=None, **extra):
    data = dict(VAST, **({"volgende": volgende} if volgende is not None else {}))
    client.post("/inloggen", data=data, **extra)
    return client.post("/inloggen/code", data={"code": code_bij(geheim, 1)})


def test_wachtwoord_en_code_gaan_naar_het_doel(app, client):
    _b, geheim = beheerder_met_wachtwoord()
    assert code_stap(client, geheim, "/log?x=1").location == "/log?x=1"


def test_zonder_doel_naar_het_rekoverzicht(app, client):
    _b, geheim = beheerder_met_wachtwoord()
    assert code_stap(client, geheim).location == "/rekoverzicht"


@pytest.mark.parametrize("doel", ["https://andere.site", "//andere.site", "/\\andere.site", "javascript:x", "/%0d%0a"])
def test_doel_buiten_de_applicatie_geeft_het_rekoverzicht(app, client, doel):
    _b, geheim = beheerder_met_wachtwoord()
    assert code_stap(client, geheim, doel).location == "/rekoverzicht"


def test_doel_in_de_halve_sessie_wordt_vlak_voor_de_redirect_opnieuw_gecontroleerd(app, client):
    """Mutant: de controle bij het lezen uit de sessie weglaten laat `//andere.site` door."""
    _b, geheim = beheerder_met_wachtwoord()
    client.post("/inloggen", data=VAST)
    with client.session_transaction() as s:
        s["volgende"] = "//andere.site"
    assert client.post("/inloggen/code", data={"code": code_bij(geheim, 1)}).location == "/rekoverzicht"


def test_mislukte_poging_houdt_het_doel_vast(app, client):
    _b, geheim = beheerder_met_wachtwoord()
    r = client.post("/inloggen", data={"gebruikersnaam": "anna", "wachtwoord": "fout!fout!fout", "volgende": "/log"})
    assert doel_van(r.location) == "/log"
    assert 'name="volgende" value="/log"' in client.get(r.location).text
    client.post("/inloggen", data=dict(VAST, volgende="/log"))
    assert client.post("/inloggen/code", data={"code": "000000"}).location == "/inloggen/code"
    assert client.post("/inloggen/code", data={"code": code_bij(geheim, 1)}).location == "/log"


def test_inlogscherm_zet_het_doel_in_het_formulier_en_de_passkeyknop(client):
    tekst = client.get("/inloggen?volgende=/boten/12").text
    assert 'name="volgende" value="/boten/12"' in tekst
    assert 'data-verifieer="/inloggen/passkey?volgende=/boten/12"' in tekst
    tekst = client.get("/inloggen?volgende=https://andere.site").text
    assert 'name="volgende"' not in tekst and "volgende=" not in tekst


def test_passkey_gaat_naar_het_doel(app, client, monkeypatch):
    b, _ = beheerder_met_wachtwoord()
    monkeypatch.setattr(beheerders, "passkey_inloggen", lambda *_: b)
    for url, verwacht in (("/inloggen/passkey?volgende=/log%3Fx%3D1", "/log?x=1"), ("/inloggen/passkey", "/rekoverzicht"),
                          ("/inloggen/passkey?volgende=//andere.site", "/rekoverzicht")):
        with client.session_transaction() as s:
            s["webauthn_challenge"] = "Y2hhbGxlbmdl"
        assert client.post(url, json={"id": "x"}).json == {"url": verwacht}, url


def test_geen_cookie_voor_wie_niet_ingelogd_is(client):
    r = client.get("/log?x=1")
    assert doel_van(r.location) == "/log?x=1" and "Set-Cookie" not in r.headers


def test_get_onthoudt_pad_en_querystring(client):
    assert doel_van(client.get("/log").location) == "/log"


def test_formulier_gebruikt_de_referer_van_dezelfde_host(client):
    r = client.post("/profiel/intrekken", headers={"Referer": "http://localhost/profiel?a=1#x"})
    assert doel_van(r.location) == "/profiel?a=1"


@pytest.mark.parametrize("referer", [None, "", "http://andere.site/profiel", "niets", "http://localhost//andere.site",
                                     "http://localhost/%2f"],
                         ids=["zonder", "leeg", "andere_host", "geen_url", "dubbele_slash", "gecodeerde_slash"])
def test_formulier_zonder_bruikbare_referer_geeft_geen_doel(client, referer):
    headers = {"Referer": referer} if referer is not None else {}
    assert client.post("/profiel/intrekken", headers=headers).location == "/inloggen"


def test_recente_inlog_geeft_het_doel_door_ook_als_json(app, client):
    _b, geheim = beheerder_met_wachtwoord()
    code_stap(client, geheim)
    referer = {"Referer": "http://localhost/profiel"}
    with client.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = client.post("/profiel/passkey/opties", json={}, headers=referer)
    assert r.status_code == 401 and doel_van(r.json["url"]) == "/profiel"
    code_stap(client, geheim)
    with client.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    assert doel_van(client.post("/profiel/intrekken", headers=referer).location) == "/profiel"


def test_kijker_op_een_pagina_die_hij_niet_mag_zien_krijgt_403(app, client):
    _b, geheim = beheerder_met_wachtwoord("kees", "kijker")
    client.post("/inloggen", data={"gebruikersnaam": "kees", "wachtwoord": WACHTWOORD, "volgende": "/log"})
    assert client.post("/inloggen/code", data={"code": code_bij(geheim, 1)}).location == "/log"
    assert client.get("/log").status_code == 403
