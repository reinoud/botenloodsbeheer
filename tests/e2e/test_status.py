"""Slice 9: technische statuspagina (BLB-037, ADR-010) en de bootaantallen in de lijst per lid en
via GET /api/v1/bootaantallen (BLB-009). draai.sh maakt een token dat over 10 dagen verloopt
(e2e-kort-<stempel>) en tokens met en zonder het recht bootaantallen:lezen."""

import json
import os
import re

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


def test_bootaantallen_api_gelijk_aan_de_lijst_per_lid(page):
    """BLB-009 criteria 2 en 3: de seed zet boten van leden op plaatsen."""
    status, _, tekst = roep(f"{API}/bootaantallen", token("lezen"))
    assert status == 200
    regel = next(r for r in json.loads(tekst) if any(r["aantallen"].values()))
    wachtwoord_instellen(page, "bootaantallen")
    page.goto(f"/leden?zoek={regel['lidnummer']}")
    lidnummer = page.locator("[data-label='Lidnummer']",
                             has_text=re.compile(f"^{re.escape(regel['lidnummer'])}$"))
    page.locator("main > ul.bl-lijst > li").filter(has=lidnummer).get_by_role("link").click()
    tabel = page.locator("h2:has-text('Aantal boten per bootsoort') + p + ul")
    getoond = dict(zip(tabel.locator("[data-label='Bootsoort']").all_inner_texts(),
                       map(int, tabel.locator("[data-label='Aantal']").all_inner_texts()),
                       strict=True))
    assert getoond == regel["aantallen"]


def test_bootaantallen_zonder_recht_403():
    """BLB-009 criterium 6, via de proxy; dit token heeft alleen leden:importeren."""
    status, _, tekst = roep(f"{API}/bootaantallen", token("api"))
    assert (status, json.loads(tekst)) == (403, {"fout": "Geen toegang."})
    assert os.environ["E2E_TOKEN_API"] not in tekst
