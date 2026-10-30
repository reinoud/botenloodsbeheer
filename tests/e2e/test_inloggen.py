"""Inloggen met passkey en met wachtwoord plus TOTP: happy en unhappy flow (BLB-022)."""

import re
import time

from conftest import WACHTWOORD, gebruikersnaam, link, uitloggen, wachtwoord_instellen
from playwright.sync_api import expect

MISLUKT = "Inloggen is mislukt"


def wachtwoord_stap(page, soort):
    page.get_by_label("Gebruikersnaam").fill(gebruikersnaam(soort))
    page.get_by_label("Wachtwoord").fill(WACHTWOORD)
    page.get_by_role("button", name="Verder").click()


def test_passkey_instellen_uitloggen_en_inloggen(page, authenticator):
    page.goto(link("passkey"))
    page.get_by_role("button", name="Passkey instellen").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Welkom")
    uitloggen(page)
    page.get_by_role("button", name="Inloggen met passkey").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Welkom")

    # Het log toont de uitnodiging en de passkey, zonder de code uit de link.
    page.get_by_role("link", name="Log").click()
    log = page.locator("section.log")
    expect(log).to_contain_text("beheerder.uitgenodigd")
    expect(log).to_contain_text("methode: passkey")
    assert link("passkey").rsplit("/", 1)[1] not in page.content()


def test_wachtwoord_en_totp_foute_code_geweigerd_juiste_code_werkt(page):
    totp = wachtwoord_instellen(page, "wachtwoord")
    uitloggen(page)
    wachtwoord_stap(page, "wachtwoord")
    goed = totp.at(time.time() + 30)  # de huidige stap is bij het instellen gebruikt
    page.get_by_label("Code van zes cijfers").fill("000000" if goed != "000000" else "111111")
    page.get_by_role("button", name="Inloggen").click()
    expect(page.get_by_role("alert")).to_contain_text(MISLUKT)
    page.get_by_label("Code van zes cijfers").fill(goed)
    page.get_by_role("button", name="Inloggen").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Welkom")


def test_vergrendeling_na_vijf_foute_wachtwoorden(page):
    wachtwoord_instellen(page, "vergrendel")
    uitloggen(page)
    for _ in range(5):
        page.get_by_label("Gebruikersnaam").fill(gebruikersnaam("vergrendel"))
        page.get_by_label("Wachtwoord").fill("dit is niet het wachtwoord")
        page.get_by_role("button", name="Verder").click()
        expect(page.get_by_role("alert")).to_contain_text(MISLUKT)
    # Ook het juiste wachtwoord wordt nu 15 minuten geweigerd, met dezelfde melding.
    wachtwoord_stap(page, "vergrendel")
    expect(page.get_by_role("alert")).to_contain_text(MISLUKT)
    expect(page.get_by_role("heading", level=1)).to_have_text("Inloggen")


def test_bezoeker_en_gebruikte_link(page):
    page.goto("/")
    expect(page).to_have_url(re.compile(r"/inloggen$"))
    wachtwoord_instellen(page, "bezoeker")  # eigen link, zodat de test ook los draait (#4)
    uitloggen(page)
    page.goto(link("bezoeker"))
    expect(page.get_by_role("alert")).to_contain_text("ongeldig, verlopen of al gebruikt")
