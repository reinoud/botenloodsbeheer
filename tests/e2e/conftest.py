"""E2E tegen de draaiende stack (architectuur §6.4). Start via tests/e2e/draai.sh, dat de
uitnodigingen aanmaakt met de echte CLI en de links als omgevingsvariabelen doorgeeft."""

import os

import pyotp
import pytest
from playwright.sync_api import expect

STEMPEL = os.environ["E2E_STEMPEL"]
WACHTWOORD = "e2e wachtwoord voor de loods"


def reknaam(letter):
    """Een reknaam van hooguit 10 tekens (ADR-003), uniek per run en per letter: de letter van de
    test plus de stempel in 36-tallig (6 tekens). draai.sh ruimt na de run de rekken op die op
    deze naam passen bij een bekende stempel (opruimen.sql, issue #142); pas die SQL aan als dit
    schema van de naam verandert."""
    cijfers, n = "", int(STEMPEL)
    while n:
        n, rest = divmod(n, 36)
        cijfers = "0123456789abcdefghijklmnopqrstuvwxyz"[rest] + cijfers
    return f"{letter}{cijfers}"


def link(soort):
    return os.environ[f"E2E_LINK_{soort.upper()}"]


def gebruikersnaam(soort):
    return f"e2e-{soort}-{STEMPEL}"


@pytest.fixture(scope="session")
def base_url():
    return os.environ["E2E_BASIS_URL"]


@pytest.fixture
def authenticator(page):
    """Virtuele authenticator van Chromium met user verification (WebAuthn via CDP)."""
    cdp = page.context.new_cdp_session(page)
    cdp.send("WebAuthn.enable")
    cdp.send("WebAuthn.addVirtualAuthenticator", {"options": {
        "protocol": "ctap2", "transport": "internal", "hasResidentKey": True,
        "hasUserVerification": True, "isUserVerified": True}})
    return cdp


def blok_openen(page, titel):
    """Opent een uitklapblok met deze titel alleen als het dicht is: een klik op een open blok klapt
    het dicht. Een `summary` telt in Playwright niet als knop, dus de titel mag gelijk zijn aan een knop."""
    dicht = page.locator("details.dj-disclosure:not([open]) > summary", has_text=titel)
    if dicht.count():
        dicht.click()


def wachtwoord_instellen(page, soort, url=None):
    """Stelt via de eigen uitnodiging van de test (of url) een wachtwoord met TOTP in; daarna
    ingelogd."""
    page.goto(url or link(soort))
    blok_openen(page, "Wachtwoord en authenticator-app")  # het blok begint dicht (BV-64)
    totp = pyotp.TOTP(page.locator("#totp-geheim").inner_text())
    page.get_by_label("Wachtwoord (12 tot 128 tekens)").fill(WACHTWOORD)
    page.get_by_label("Wachtwoord nog een keer").fill(WACHTWOORD)
    page.get_by_label("Code van zes cijfers uit de app").fill(totp.now())
    page.get_by_role("button", name="Wachtwoord instellen").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Rekoverzicht")
    return totp


def uitloggen(page):
    page.get_by_role("button", name="Uitloggen").click()
    expect(page.get_by_text("Je bent uitgelogd.")).to_be_visible()
