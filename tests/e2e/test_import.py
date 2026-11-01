"""Slice 6: de import van leden via Traefik en de integratiecontainer (ADR-012, ADR-013;
BLB-006, 007, 032, 034, 041). De container deelt het netwerk van traefik en roept E2E_API_URL aan
(zie test_api.py). Twee inlogverzoeken. Een test die de leden wijzigt, zet de fixture terug."""

import http.client
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from conftest import wachtwoord_instellen
from playwright.sync_api import expect

API = os.environ["E2E_API_URL"]
FIXTURE = json.loads(Path("/fixtures/leden.json").read_text(encoding="utf-8"))


def roep(methode, pad, gegevens=None, soort="import", ruw=None):
    """Geeft (status, json)."""
    lichaam = ruw if ruw is not None else (
        json.dumps(gegevens).encode() if gegevens is not None else None)
    verzoek = urllib.request.Request(
        f"{API}{pad}", data=lichaam, method=methode,
        headers={"Authorization": f"Bearer {os.environ[f'E2E_TOKEN_{soort.upper()}']}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(verzoek, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as fout:
        return fout.code, json.loads(fout.read())


def test_fixture_importeren_en_veiligheidsgrens():
    """BLB-006 criterium 1, BLB-007 criterium 1, BLB-034 criterium 3, BLB-007 criterium 4."""
    status, uitkomst = roep("PUT", "/leden", {"leden": FIXTURE})
    assert status == 200 and (uitkomst["ontvangen"], uitkomst["overgeslagen"]) == (210, 2)
    status, antwoord = roep("PUT", "/leden", {"leden": FIXTURE[:90]})
    assert status == 409 and "minder dan de helft" in antwoord["fout"]
    status, uitkomst = roep("PUT", "/leden", {"leden": FIXTURE})
    assert status == 200 and uitkomst["uit_bron"] == 0 and uitkomst["bijgewerkt"] == 0


def test_vorm_en_grootte_via_traefik():
    """BLB-007 criterium 3: 422 en 413. Tot 3 MB laat Traefik het verzoek door en geeft de
    applicatie de 413 als JSON; daarboven weigert Traefik zelf (ADR-013)."""
    assert roep("PUT", "/leden", {"leden": "geen lijst"})[0] == 422
    assert roep("PUT", "/leden", {"leden": [{"lidnummer": "1"}] * 5001})[0] == 422
    groot = json.dumps({"leden": [{"lidnummer": str(n), "naam": "x" * 600}
                                  for n in range(4000)]}).encode()
    assert len(groot) > 2 * 1024 * 1024
    assert len(groot) < 3 * 1024 * 1024
    assert roep("PUT", "/leden", ruw=groot) == (413, {"fout": "Het verzoek is groter dan 2 MB."})
    # Traefik weigert op Content-Length, vóór het lichaam; daarom alleen de kop sturen.
    deel = urlsplit(API)
    verbinding = http.client.HTTPConnection(deel.hostname, deel.port, timeout=30)
    verbinding.putrequest("PUT", f"{deel.path}/leden")
    verbinding.putheader("Authorization", f"Bearer {os.environ['E2E_TOKEN_IMPORT']}")
    verbinding.putheader("Content-Length", str(3 * 1024 * 1024 + 1))
    verbinding.endheaders()
    antwoord = verbinding.getresponse()
    assert antwoord.status == 413 and b"fout" not in antwoord.read()
    verbinding.close()
    assert roep("POST", "/leden/import-mislukt", {"reden": "vrije tekst"})[0] == 422


def test_zonder_recht_403():
    """BLB-032 criterium 2."""
    assert roep("PUT", "/leden", {"leden": FIXTURE}, soort="lezen") == (403, {"fout": "Geen toegang."})
    assert roep("GET", "/leden/importverzoek", soort="lezen")[0] == 403


def test_beheerder_vraagt_import_aan_en_ziet_de_uitkomst(page):
    """BLB-006 criterium 5: de integratiecontainer begint binnen een minuut."""
    wachtwoord_instellen(page, "import")
    page.goto("/leden")
    page.get_by_role("button", name="Leden nu ophalen").click()
    expect(page.get_by_text("De import is aangevraagd.")).to_be_visible()
    nieuwste = page.locator("section.kaart table tbody tr").first
    expect(nieuwste.locator("td[data-label='Status']")).to_have_text("aangevraagd")
    assert roep("GET", "/leden/importverzoek") == (200, {"aangevraagd": True})
    einde = datetime.now() + timedelta(seconds=75)
    while datetime.now() < einde:
        page.wait_for_timeout(5000)
        page.reload()
        if nieuwste.locator("td[data-label='Status']").inner_text() != "aangevraagd":
            break
    expect(nieuwste.locator("td[data-label='Status']")).to_have_text("geslaagd")
    expect(nieuwste.locator("td[data-label='Resultaat']")).to_contain_text("ontvangen: 210")


def test_boten_van_leden_die_gaan_opzeggen(page):
    """BLB-041 criterium 3: alle leden zeggen op 31-12-2099 op; de seed heeft boten met een
    plaats. Daarna gaat de fixture terug."""
    wachtwoord_instellen(page, "opzeggend")
    later = [r | {"opzegdatum": "2099-12-31"} if not r["opzegdatum"] else r for r in FIXTURE]
    try:
        assert roep("PUT", "/leden", {"leden": later})[0] == 200
        page.get_by_role("link", name="Gaan opzeggen").click()
        rijen = page.locator("main > table tbody tr")
        expect(rijen.first).to_be_visible()
        assert set(rijen.locator("td[data-label='Opzegdatum']").all_inner_texts()) == {"31-12-2099"}
        eerste = rijen.first.locator("td").all_inner_texts()
        assert len(eerste) == 5 and re.fullmatch(r"Rek \w+", eerste[2])
    finally:
        assert roep("PUT", "/leden", {"leden": FIXTURE})[0] == 200
    page.reload()
    expect(page.get_by_text("Er zijn geen boten van leden die gaan opzeggen.")).to_be_visible()
