"""E2E tegen de draaiende stack (architectuur §6.4). Start via tests/e2e/draai.sh, dat de
uitnodigingen aanmaakt met de echte CLI en de links als omgevingsvariabelen doorgeeft."""

import os

import pytest

STEMPEL = os.environ["E2E_STEMPEL"]


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
