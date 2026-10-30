"""E2E tegen de draaiende stack (architectuur §6.4). Start via tests/e2e/draai.sh, dat de
uitnodigingen aanmaakt met de echte CLI en de links als omgevingsvariabelen doorgeeft."""

import os

import pyotp
import pytest
from playwright.sync_api import expect

STEMPEL = os.environ["E2E_STEMPEL"]
WACHTWOORD = "e2e wachtwoord voor de loods"


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


def wachtwoord_instellen(page, soort):
    """Stelt via de eigen uitnodiging van de test een wachtwoord met TOTP in; daarna ingelogd."""
    page.goto(link(soort))
    totp = pyotp.TOTP(page.locator("#totp-geheim").inner_text())
    page.get_by_label("Wachtwoord (12 tot 128 tekens)").fill(WACHTWOORD)
    page.get_by_label("Wachtwoord nog een keer").fill(WACHTWOORD)
    page.get_by_label("Code van zes cijfers uit de app").fill(totp.now())
    page.get_by_role("button", name="Wachtwoord instellen").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("Welkom")
    return totp


def uitloggen(page):
    page.get_by_role("button", name="Uitloggen").click()
    expect(page.get_by_text("Je bent uitgelogd.")).to_be_visible()
