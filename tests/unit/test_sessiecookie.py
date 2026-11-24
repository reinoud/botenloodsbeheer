"""Set-Cookie alleen bij een gewijzigde sessie, zodat een laat antwoord geen oudere sessie terugzet (#402, #419)."""

import time

from tests.unit.hulp import beheerder_met_wachtwoord
from tests.unit.test_web import inloggen


def _sessie(client):
    b, _ = beheerder_met_wachtwoord("bert")
    with client.session_transaction() as s:
        # Met een csrf_token, zoals na de eerste pagina; anders zet de pagina die nog en wijzigt de sessie.
        s.update(beheerder_id=b.id, sessieversie=b.sessieversie, ingelogd_op=time.time(), csrf_token="vast")
        s.permanent = True


def _ingelogd(client):
    with client.session_transaction() as s:
        return "beheerder_id" in s


def test_statisch_bestand_met_sessie_geeft_geen_set_cookie(app, client):
    _sessie(client)
    r = client.get("/static/menu.js")
    assert r.status_code == 200 and "Set-Cookie" not in r.headers


def test_gewone_pagina_met_ongewijzigde_sessie_geeft_geen_set_cookie(app, client):
    _sessie(client)
    r = client.get("/log")
    assert r.status_code == 200 and "Set-Cookie" not in r.headers


def test_inloggen_zet_de_cookie_en_uitloggen_wist_de_inlog(app, client):
    _b, geheim = beheerder_met_wachtwoord()
    r = inloggen(client, geheim)
    assert r.location == "/rekoverzicht" and "Set-Cookie" in r.headers and _ingelogd(client)
    r = client.post("/uitloggen")
    assert "Set-Cookie" in r.headers and not _ingelogd(client)


def test_ongeldige_sessie_wordt_gewist(app, client):
    _sessie(client)
    with client.session_transaction() as s:
        s["sessieversie"] += 1
    r = client.get("/log")
    assert r.location.startswith("/inloggen") and "Set-Cookie" in r.headers and not _ingelogd(client)
