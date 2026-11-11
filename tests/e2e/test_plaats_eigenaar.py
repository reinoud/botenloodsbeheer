"""Issue #234, de route voor een mens: op het scherm van een plaats met een boot van een lid is de
naam van de eigenaar een link naar het lid."""

import re

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, rek_met_plaats, toewijzen


def test_plaats_eigenaar_linkt_naar_het_lid(page):
    wachtwoord_instellen(page, "plaatseigenaar")
    rek = reknaam("f")
    bootnaam = f"Boot {rek}"
    code = rek_met_plaats(page, rek, ["Kajak"])
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2)
    toewijzen(page, code, bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()

    page.goto("/indeling")
    page.get_by_role("link", name=code, exact=True).click()
    naam = page.locator("[data-veld=naam]").inner_text()
    page.locator("[data-veld=naam]").get_by_role("link", name=naam, exact=True).click()
    expect(page).to_have_url(re.compile(r"/leden/\d+$"))
    expect(page.get_by_role("heading", level=1)).to_have_text(naam)
    expect(page.get_by_role("link", name=bootnaam, exact=True)).to_be_visible()  # het lid heeft de boot van de plaats
