"""Beheerders beheren (BLB-023) en eigen inlogmethodes toevoegen of intrekken (BLB-038, issue #2).
Elke test heeft een eigen uitnodiging uit draai.sh en draait ook los."""

import re

from conftest import (
    STEMPEL,
    WACHTWOORD,
    blok_openen,
    gebruikersnaam,
    uitloggen,
    wachtwoord_instellen,
)
from playwright.sync_api import expect

MISLUKT = "Inloggen is mislukt"


def wachtwoord_inloggen(page, naam):
    blok_openen(page, "Met wachtwoord en code")  # na een mislukte poging staat het blok al open
    page.get_by_label("Gebruikersnaam").fill(naam)
    page.get_by_label("Wachtwoord").fill(WACHTWOORD)
    page.get_by_role("button", name="Verder").click()


def passkey_toevoegen(page):
    page.get_by_role("link", name="Profiel").click()
    blok_openen(page, "passkey")  # "Passkey toevoegen" zonder passkey, "Nog een passkey" met een
    page.get_by_role("button", name="Passkey toevoegen").click()
    expect(page.get_by_text("De passkey is toegevoegd.")).to_be_visible()


def test_beide_methodes_wachtwoord_vergrendeld_passkey_slaagt(page, authenticator):
    """Issue #2: een vergrendeld wachtwoord sluit een beheerder met passkey niet buiten."""
    wachtwoord_instellen(page, "methodes")
    passkey_toevoegen(page)
    page.goto("/log/techniek")
    expect(page.locator("section.log")).to_contain_text("beheerder.methode_toegevoegd")
    uitloggen(page)
    for _ in range(5):
        blok_openen(page, "Met wachtwoord en code")
        page.get_by_label("Gebruikersnaam").fill(gebruikersnaam("methodes"))
        page.get_by_label("Wachtwoord").fill("dit is niet het wachtwoord")
        page.get_by_role("button", name="Verder").click()
        expect(page.get_by_role("alert")).to_contain_text(MISLUKT)
    wachtwoord_inloggen(page, gebruikersnaam("methodes"))
    expect(page.get_by_role("alert")).to_contain_text(MISLUKT)  # vergrendeld
    page.get_by_role("button", name="Inloggen met passkey").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Rekoverzicht")


def test_methode_intrekken_beeindigt_sessie_laatste_blijft(page, authenticator):
    wachtwoord_instellen(page, "intrekken")
    passkey_toevoegen(page)
    page.get_by_role("button", name="Wachtwoord intrekken").click()
    expect(page.get_by_text("De inlogmethode is ingetrokken.")).to_be_visible()
    expect(page.get_by_role("heading", level=1)).to_have_text("Inloggen")
    wachtwoord_inloggen(page, gebruikersnaam("intrekken"))
    expect(page.get_by_role("alert")).to_contain_text(MISLUKT)
    page.get_by_role("button", name="Inloggen met passkey").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Rekoverzicht")
    page.get_by_role("link", name="Profiel").click()
    page.get_by_role("button", name="Passkey 1 intrekken").click()
    expect(page.get_by_role("alert")).to_contain_text("Dit is je enige inlogmethode")
    page.goto("/log/techniek")
    log = page.locator("section.log")
    expect(log).to_contain_text("beheerder.methode_ingetrokken")
    expect(log).to_contain_text("methode: wachtwoord en TOTP")


def test_uitnodigen_herstellen_en_blokkeren(page, browser, base_url):
    wachtwoord_instellen(page, "beheerders")
    nieuw = f"e2e-nieuw-{STEMPEL}"
    page.get_by_role("link", name="Beheerders").click()
    page.get_by_label("Gebruikersnaam").fill(nieuw)
    page.get_by_role("button", name="Uitnodigen").click()
    link = page.locator("#uitnodigingslink").inner_text()

    collega = browser.new_context(base_url=base_url).new_page()
    wachtwoord_instellen(collega, None, url=link)

    # Herstel: de oude methodes en de sessie van de collega vervallen; een nieuwe link werkt.
    page.goto("/beheerders")
    page.get_by_role("button", name=f"Toegang herstellen: {nieuw}").click()
    herstel = page.locator("#uitnodigingslink").inner_text()
    collega.goto("/")
    expect(collega).to_have_url(re.compile(r"/inloggen$"))
    wachtwoord_instellen(collega, None, url=herstel)

    # Blokkeren beëindigt de sessie en inloggen lukt niet meer.
    page.goto("/beheerders")
    page.get_by_role("button", name=f"Blokkeren: {nieuw}").click()
    expect(page.get_by_text("Het account is geblokkeerd.")).to_be_visible()
    collega.goto("/")
    expect(collega).to_have_url(re.compile(r"/inloggen$"))
    wachtwoord_inloggen(collega, nieuw)
    expect(collega.get_by_role("alert")).to_contain_text(MISLUKT)

    # Het eigen account heeft geen knoppen: zo blijft er altijd een actieve beheerder.
    eigen = gebruikersnaam("beheerders")
    expect(page.get_by_role("button", name=f"Blokkeren: {eigen}")).to_have_count(0)
    page.goto("/log/techniek")
    expect(page.locator("section.log")).to_contain_text("beheerder.geblokkeerd")
    collega.context.close()
