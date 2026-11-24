"""Een statisch bestand zet geen sessiecookie; een gewone pagina wel, zodat de sessie schuift (#402)."""

import time

from tests.unit.hulp import beheerder_met_wachtwoord


def _sessie(client):
    b, _ = beheerder_met_wachtwoord("bert")
    with client.session_transaction() as s:
        s.update(beheerder_id=b.id, sessieversie=b.sessieversie, ingelogd_op=time.time())
        s.permanent = True


def test_statisch_bestand_met_sessie_geeft_geen_set_cookie(app, client):
    _sessie(client)
    r = client.get("/static/menu.js")
    assert r.status_code == 200 and "Set-Cookie" not in r.headers


def test_gewone_pagina_met_sessie_geeft_wel_set_cookie(app, client):
    _sessie(client)
    r = client.get("/log")
    assert r.status_code == 200 and "Set-Cookie" in r.headers
