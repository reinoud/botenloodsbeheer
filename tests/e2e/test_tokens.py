"""Slice 10: de tokenschermen en de leesaanroepen (ADR-005 v1.4.0, ADR-012 v1.6.0; BLB-030,
BLB-032, BLB-035). Een persoonlijk token met de voorgevulde whitelist (KOPPELNET) werkt via het
entrypoint intern, zoals de route in issue #51. Twee inloggen per test, ruim onder de grens."""

import json
import os

from conftest import gebruikersnaam, uitloggen, wachtwoord_instellen
from playwright.sync_api import expect
from test_api import API, roep


def token_maken(page, naam, rechten, soort="Persoonlijk"):
    page.get_by_role("link", name="Tokens").click()
    page.get_by_role("link", name="Token maken").click()
    page.get_by_role("radio", name=soort).check()
    page.get_by_label("Naam (a-z, cijfers, punt, - en _)").fill(naam)
    for recht in rechten:
        page.get_by_label(recht, exact=True).check()
    page.get_by_role("button", name="Token maken").click()
    expect(page.get_by_role("heading", level=1)).to_have_text(f"Token {naam} gemaakt")
    return page.locator("#tokenwaarde").inner_text()


def rij(page, naam):
    return page.locator("tr", has=page.locator('td[data-label="Naam"]', has_text=naam))


def test_persoonlijk_token_maken_wijzigen_en_intrekken(page):
    """De route uit issue #51: boten zonder adres, leden 403, na leden:lezen 200 met logregel,
    na intrekken 401. De waarde staat één keer op het scherm."""
    wachtwoord_instellen(page, "tokens")
    naam = f"e2e-pers-{os.environ['E2E_STEMPEL']}"
    waarde = token_maken(page, naam, ["boten:lezen"])
    assert waarde.startswith("blb_")

    status, _, tekst = roep(f"{API}/boten", waarde)
    assert status == 200
    eigenaren = [b["eigenaar"] for b in json.loads(tekst) if b["eigenaar"]]
    assert eigenaren and all(set(e) == {"lidnummer", "naam"} for e in eigenaren)
    assert roep(f"{API}/leden", waarde)[0] == 403

    page.get_by_role("link", name="Terug naar tokens").click()
    expect(page.get_by_text(waarde)).to_have_count(0)
    regel = rij(page, naam)
    expect(regel.locator('td[data-label="Soort"]')).to_have_text("persoonlijk")
    expect(regel.locator('td[data-label="Eigenaar of maker"]')).to_have_text(
        gebruikersnaam("tokens"))
    wijzigen = page.locator("details", has=page.locator("summary", has_text=naam))
    wijzigen.locator("summary").click()
    wijzigen.get_by_label("leden:lezen", exact=True).check()
    wijzigen.get_by_role("button", name=f"Rechten opslaan: {naam}").click()
    expect(page.get_by_text("De rechten zijn gewijzigd.")).to_be_visible()
    status, _, tekst = roep(f"{API}/leden", waarde)
    assert status == 200 and "adres" not in json.loads(tekst)[0]

    page.get_by_role("link", name="Technisch log").click()
    expect(page.locator("li", has_text="token.rechten_gewijzigd").first).to_contain_text(naam)

    page.get_by_role("link", name="Tokens").click()
    rij(page, naam).get_by_role("button", name=f"Intrekken: {naam}").click()
    expect(page.get_by_text("Het token is ingetrokken.")).to_be_visible()
    assert roep(f"{API}/boten", waarde)[0] == 401


def test_token_van_een_collega_intrekken(page, browser, base_url):
    """BLB-035 criterium 2: een collega maakt een token, deze beheerder trekt het in."""
    collega = browser.new_context(base_url=base_url).new_page()
    wachtwoord_instellen(collega, "tokenscollega")
    naam = f"e2e-collega-{os.environ['E2E_STEMPEL']}"
    waarde = token_maken(collega, naam, ["plaatsen:lezen"])
    assert roep(f"{API}/plaatsen", waarde)[0] == 200
    uitloggen(collega)
    collega.context.close()

    wachtwoord_instellen(page, "tokensintrekken")
    page.get_by_role("link", name="Tokens").click()
    expect(rij(page, naam).locator('td[data-label="Eigenaar of maker"]')).to_have_text(
        gebruikersnaam("tokenscollega"))
    rij(page, naam).get_by_role("button", name=f"Intrekken: {naam}").click()
    expect(page.get_by_text("Het token is ingetrokken.")).to_be_visible()
    expect(rij(page, naam).locator('td[data-label="Intrekken"]')).to_contain_text("Ingetrokken op")
    assert roep(f"{API}/plaatsen", waarde)[0] == 401
