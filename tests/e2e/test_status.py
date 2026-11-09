"""Slice 9: technische statuspagina (BLB-037, ADR-010) en de bootaantallen via GET /api/v1/bootaantallen (BLB-009).
draai.sh maakt een token dat over 10 dagen verloopt
(e2e-kort-<stempel>) en tokens met en zonder het recht bootaantallen:lezen."""

import json
import os
import re
from collections import Counter

from conftest import STEMPEL, wachtwoord_instellen
from playwright.sync_api import expect
from test_api import API, roep, token


def test_statuspagina_html_en_json_met_tokenwaarschuwing(page):
    """BLB-037 criteria 1, 4 en 5. Of de opschoning al draaide, hangt af van de klok
    (OPSCHOON_TIJDSTIP); de unittests dekken tijdstip en aantallen (BLB-026 criterium 5)."""
    wachtwoord_instellen(page, "status")
    page.get_by_role("navigation").get_by_role("link", name="Status").click()
    expect(page.get_by_role("heading", name="Technische status")).to_be_visible()
    waarschuwing = page.get_by_role("alert")
    expect(waarschuwing).to_contain_text(f"e2e-kort-{STEMPEL} (robot), vervalt op")
    for onderdeel in ("Database", "Worker", "Import van leden", "Opschoning", "API",
                      "Bootaantallen"):
        expect(page.locator("td[data-label='Onderdeel']", has_text=onderdeel).first).to_be_visible()
    expect(page.locator("main")).to_contain_text("Laatste opschoning:")

    antwoord = page.request.get("/status.json")
    assert antwoord.ok and antwoord.headers["content-type"] == "application/json"
    s = antwoord.json()
    assert s["database"]["status"] == "ok" and s["api"]["ingeschakeld"] is True
    assert s["opschoning"]["status"] == "ok"
    assert f"e2e-kort-{STEMPEL}" in [t["naam"] for t in s["tokens_verlopen"]["tokens"]]
    assert s["import"]["laatst_geslaagd"] is not None
    for tekst in (antwoord.text(), page.content()):
        assert token("lezen") not in tekst and "blb_" not in tekst


def test_status_zonder_inloggen_naar_inloggen(page):
    page.goto("/status.json")
    expect(page.get_by_role("heading", name="Inloggen")).to_be_visible()
    assert "database" not in page.content()


def test_bootaantallen_api_gelijk_aan_de_boten_met_plaats(page):
    """BLB-009 criterium 2 en issue #179: de API telt de boten met een plaats op de lidpagina."""
    status, _, tekst = roep(f"{API}/bootaantallen", token("lezen"))
    assert status == 200
    regels = [r for r in json.loads(tekst) if any(r["aantallen"].values())]
    assert regels
    wachtwoord_instellen(page, "bootaantallen")
    for regel in regels:  # een lid met een boot zonder plaats vangt een telling die die boot meetelt
        page.goto(f"/leden?zoek={regel['lidnummer']}")
        lidnummer = page.locator("[data-label='Lidnummer']",
                                 has_text=re.compile(f"^{re.escape(regel['lidnummer'])}$"))
        page.locator("main > ul.bl-lijst > li").filter(has=lidnummer).get_by_role("link").click()
        expect(page.get_by_role("heading", name="Aantal boten per bootsoort")).to_have_count(0)
        # Alleen boten met een plaats tellen: de plaats is een link, "Geen plaats" niet.
        met_plaats = page.locator("li.bl-item").filter(has=page.locator("a[data-label='Plaats']"))
        getoond = Counter(met_plaats.locator("[data-label='Bootsoort']").all_inner_texts())
        assert {s: getoond[s] for s in regel["aantallen"]} == regel["aantallen"], regel["lidnummer"]


def test_bootaantallen_zonder_recht_403():
    """BLB-009 criterium 6, via de proxy; dit token heeft alleen leden:importeren."""
    status, _, tekst = roep(f"{API}/bootaantallen", token("api"))
    assert (status, json.loads(tekst)) == (403, {"fout": "Geen toegang."})
    assert os.environ["E2E_TOKEN_API"] not in tekst
