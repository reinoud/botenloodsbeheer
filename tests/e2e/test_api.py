"""Slice 5: de API via het entrypoint intern van Traefik op poort 8081 (ADR-005, ADR-012,
ADR-013; BLB-029, 033, 034). Geen browser en geen inlogverzoeken. De tokens maakt draai.sh met de
CLI in web; de container deelt het netwerk van traefik en roept E2E_API_URL aan, het adres van
traefik op koppeling, dat ook de afzender is."""

import json
import os
import urllib.error
import urllib.request

API = os.environ["E2E_API_URL"]
PUBLIEK = os.environ["E2E_BASIS_URL"]


def token(soort):
    return os.environ[f"E2E_TOKEN_{soort.upper()}"]


def roep(url, waarde=None, **kop):
    """Geeft (status, headers, tekst)."""
    verzoek = urllib.request.Request(url, headers=({"Authorization": f"Bearer {waarde}"}
                                                   if waarde else {}) | kop)
    try:
        with urllib.request.urlopen(verzoek, timeout=5) as r:
            return r.status, r.headers, r.read().decode()
    except urllib.error.HTTPError as fout:
        return fout.code, fout.headers, fout.read().decode()


def test_ik_via_de_interne_server():
    """BLB-029 criterium 1, BLB-033 criterium 1."""
    status, _, tekst = roep(f"{API}/ik", token("api"))
    assert status == 200
    antwoord = json.loads(tekst)
    assert antwoord["token"].startswith("e2e-api-") and antwoord["rechten"] == ["leden:importeren"]


def test_publieke_server_kent_de_api_niet():
    """BLB-029 criterium 4: geen API-antwoord, ook niet met een geldig token."""
    status, headers, tekst = roep(f"{PUBLIEK}/api/v1/ik", token("api"))
    assert status == 404 and "json" not in headers["Content-Type"]
    assert "leden:importeren" not in tekst


def test_intern_alleen_vanaf_koppeling():
    """ADR-013: de router op intern vraagt een adres uit KOPPELNET; 127.0.0.1 hoort daar niet bij."""
    status, _, tekst = roep("http://localhost:8081/api/v1/ik", token("api"))
    assert status == 404 and "leden:importeren" not in tekst


def test_weigeringen():
    """BLB-034 criterium 1, BLB-033 criterium 2 (adres niet op de whitelist), intrekken."""
    for waarde in (None, "blb_onzin", token("vervalst"), token("ingetrokken")):
        status, _, tekst = roep(f"{API}/ik", waarde)
        assert (status, json.loads(tekst)) == (401, {"fout": "Geen toegang."})


def test_vervalst_adres_in_de_header_telt_niet():
    """ADR-013: Traefik overschrijft X-Forwarded-For; Gunicorn laat X_Forwarded_For vallen.
    Het token staat alleen 10.203.0.99 toe, dus beide pogingen geven 401."""
    for kop in ({"X-Forwarded-For": "10.203.0.99"}, {"X_Forwarded_For": "10.203.0.99"}):
        status, _, tekst = roep(f"{API}/ik", token("vervalst"), **kop)
        assert (status, json.loads(tekst)) == (401, {"fout": "Geen toegang."}), kop


def test_boven_60_per_minuut_429_met_retry_after():
    """BLB-034 criterium 4. Zonder de grens slagen alle 15 aanroepen; met de grens (1 per
    seconde, burst 10) komt er een 429 van Traefik, zonder Content-Type (ADR-013). Een ander token
    van hetzelfde adres werkt dan nog."""
    statussen, retry = [], None
    for _ in range(15):
        status, headers, tekst = roep(f"{API}/ik", token("tempo"))
        statussen.append(status)
        if status == 429:
            retry = headers["Retry-After"]
            assert tekst == "Too Many Requests"
    assert statussen[0] == 200 and 429 in statussen, statussen
    assert set(statussen) == {200, 429}
    assert retry == "1"
    assert roep(f"{API}/ik", token("api"))[0] == 200


def test_nep_geheim_met_dezelfde_prefix_remt_het_echte_token_niet():
    """AEG-01: de sleutel van de grens is de hele header, niet de prefix. Wie alleen de prefix
    kent, raakt met een nep-geheim de grens en remt daarmee het echte token niet."""
    echt = token("prefix")
    nep = echt[:12] + "A" * 52
    assert nep != echt
    statussen = [roep(f"{API}/ik", nep)[0] for _ in range(15)]
    assert set(statussen) == {401, 429}, statussen
    assert roep(f"{API}/ik", echt)[0] == 200
