"""Vangnet (#418): één fase van tests/e2e/vangnet.sh. Dat script stopt en start web en api (de
e2e-container heeft geen docker) en roept pytest aan met E2E_VANGNET_FASE: gewoon, web_uit,
api_uit of hersteld. Elke fase wacht tot Traefik de routers heeft bijgewerkt."""

import http.client
import json
import os
import time
import urllib.parse

FASE = os.environ.get("E2E_VANGNET_FASE", "")
PUBLIEK = urllib.parse.urlsplit(os.environ["E2E_BASIS_URL"])
API = urllib.parse.urlsplit(os.environ["E2E_API_URL"])


def roep(basis, pad, accept=None, methode="GET"):
    """Geeft (status, headers, tekst); volgt geen redirect: het vangnet stuurt er geen."""
    kop = {"Accept": accept} if accept else {}
    v = http.client.HTTPConnection(basis.hostname, basis.port, timeout=5)
    v.request(methode, pad, headers=kop)
    r = v.getresponse()
    return r.status, r, r.read().decode()


def tot(controle, seconden=40):
    """Traefik neemt een gestopte of gestarte container binnen enkele seconden over."""
    einde = time.monotonic() + seconden
    while True:
        try:
            return controle()
        except (AssertionError, OSError):  # kort na de stop sluit Traefik de verbinding of laat hem hangen
            if time.monotonic() > einde:
                raise
            time.sleep(1)


def is_vangnet(status, r, tekst, html):
    assert status == 503, (status, tekst[:80])
    assert r.getheader("Retry-After") and r.getheader("Cache-Control") == "no-store"
    assert r.getheader("Content-Security-Policy") and r.getheader("X-Content-Type-Options") == "nosniff"
    if html:
        assert r.getheader("Content-Type").startswith("text/html") and "<h1>" in tekst
    else:
        assert r.getheader("Content-Type").startswith("application/json")
        assert json.loads(tekst)["fout"]


def app_antwoordt_web():
    status, r, tekst = roep(PUBLIEK, "/inloggen", "text/html")
    assert status == 200 and r.getheader("Retry-After") is None and "<h1>" in tekst, status


def app_antwoordt_api():
    status, r, tekst = roep(API, API.path + "/ik")  # zonder token: 401 van de app zelf
    assert status == 401 and json.loads(tekst)["fout"] == "Geen toegang.", (status, tekst[:80])


def test_fase():
    if FASE in ("gewoon", "hersteld"):
        tot(app_antwoordt_web)
        tot(app_antwoordt_api)
        # Publiek /api/ heeft geen router van de app; daar blijft de 404 van Traefik (#418).
        assert roep(PUBLIEK, "/api/v1/ik")[0] == 404
    elif FASE == "web_uit":
        tot(lambda: is_vangnet(*roep(PUBLIEK, "/inloggen", "text/html"), html=True))
        tot(lambda: is_vangnet(*roep(PUBLIEK, "/boten/zoeken", "application/json"), html=False))
        tot(lambda: is_vangnet(*roep(PUBLIEK, "/inloggen", methode="POST"), html=False))
        tot(app_antwoordt_api)  # de API draait nog: het vangnet neemt haar route niet over
    elif FASE == "api_uit":
        tot(lambda: is_vangnet(*roep(API, API.path + "/ik"), html=False))
        tot(app_antwoordt_web)
    else:
        raise AssertionError(f"E2E_VANGNET_FASE onbekend: {FASE!r}; draai tests/e2e/vangnet.sh")
