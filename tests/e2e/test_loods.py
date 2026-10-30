"""Indeling, boot, toewijzen, log en openbare pagina (BLB-001, 005, 010, 012, 020, 025).

Elke test maakt eigen rekken, plaatsen en boten met de stempel van de run, zodat hij los en in
elke volgorde draait. De leden komen uit flask seed (draai.sh)."""

import re
import struct
import zlib

from conftest import STEMPEL, uitloggen, wachtwoord_instellen
from playwright.sync_api import expect


def png(breedte=8, hoogte=6):
    """Een kleine, geldige PNG zonder Pillow (het Playwright-image heeft het niet)."""
    def blok(soort, data):
        return (struct.pack(">I", len(data)) + soort + data
                + struct.pack(">I", zlib.crc32(soort + data)))
    rij = b"\x00" + b"\xc8\x50\x28" * breedte
    return (b"\x89PNG\r\n\x1a\n"
            + blok(b"IHDR", struct.pack(">IIBBBBB", breedte, hoogte, 8, 2, 0, 0, 0))
            + blok(b"IDAT", zlib.compress(rij * hoogte)) + blok(b"IEND", b""))


def rek_met_plaats(page, rek, code, soorten, club=False):
    page.goto("/indeling")
    page.get_by_label("Naam van het rek").fill(rek)
    page.get_by_role("button", name="Rek aanmaken").click()
    expect(page.get_by_text("Het rek is aangemaakt.")).to_be_visible()
    sectie = page.locator("section.kaart", has=page.get_by_role("heading", name=rek, exact=True))
    sectie.get_by_text(f"Plaats toevoegen aan {rek}").click()
    sectie.get_by_label("Plaatscode").fill(code)
    for soort in soorten:
        sectie.get_by_label(soort, exact=True).check()
    if club:
        sectie.get_by_label("Clubplaats (alleen voor clubboten)").check()
    sectie.get_by_role("button", name="Plaats aanmaken").click()
    expect(page.get_by_text("De plaats is aangemaakt.")).to_be_visible()


def boot_vastleggen(page, naam, soort, eigenaar_index=None, foto=None):
    """eigenaar_index None is een clubboot; anders de positie in de ledenlijst."""
    page.goto("/boten")
    page.get_by_label("Naam van de boot").fill(naam)
    page.get_by_label("Bootsoort").select_option(label=soort)
    eigenaar = page.get_by_label("Eigenaar")
    if eigenaar_index is None:
        eigenaar.select_option(value="club")
    else:
        eigenaar.select_option(index=eigenaar_index)
    if foto:
        page.get_by_label("Foto (JPEG, PNG of WebP, niet verplicht)").set_input_files(
            {"name": "boot.png", "mimeType": "image/png", "buffer": foto})
    page.get_by_role("button", name="Boot vastleggen").click()
    expect(page.get_by_text("De boot is vastgelegd.")).to_be_visible()


def toewijzen(page, code, bootnaam):
    page.goto("/indeling")
    page.get_by_role("link", name=code, exact=True).click()
    keuze = page.locator("#boot option", has_text=bootnaam).get_attribute("value")
    page.get_by_label("Boot zonder plaats").select_option(value=keuze)
    page.get_by_role("button", name="Plaats toewijzen").click()


def test_indeling_boot_toewijzen_log_en_openbare_pagina(page):
    wachtwoord_instellen(page, "indeling")
    rek, code, bootnaam = f"E2E rek {STEMPEL}", f"E{STEMPEL}", f"Boot {STEMPEL}"
    rek_met_plaats(page, rek, code, ["Kajak"])
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2, foto=png())
    expect(page.get_by_role("img", name=f"Foto van {bootnaam}")).to_be_visible()

    toewijzen(page, code, bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    expect(page.locator("section.log")).to_contain_text("plaats.toegewezen")
    prive = {veld: page.locator(f"[data-veld={veld}]").inner_text()
             for veld in ("naam", "lidnummer", "adres", "telefoon", "email")}
    assert all(prive.values())
    openbare_link = page.locator("#openbare-link").get_attribute("href")
    assert code not in openbare_link

    uitloggen(page)
    page.goto(openbare_link)
    expect(page.get_by_role("heading", level=1)).to_have_text(f"Plaats {code}")
    expect(page.get_by_text(bootnaam)).to_be_visible()
    expect(page.get_by_text(prive["naam"], exact=True)).to_be_visible()
    expect(page.get_by_role("img", name=f"Foto van {bootnaam}")).to_be_visible()
    expect(page.locator("section.log")).to_have_count(0)
    html = page.content()
    for veld in ("lidnummer", "adres", "telefoon", "email"):
        assert prive[veld] not in html, veld

    page.goto("/p/bestaatniet")
    expect(page.get_by_role("heading", level=1)).to_have_text("Deze pagina bestaat niet")
    page.goto("/indeling")
    expect(page).to_have_url(re.compile(r"/inloggen$"))


def test_clubboot_op_ledenplaats_en_verkeerde_bootsoort_geweigerd(page):
    wachtwoord_instellen(page, "regels")
    rek, code = f"E2E regels {STEMPEL}", f"R{STEMPEL}"
    rek_met_plaats(page, rek, code, ["Supboard"])
    boot_vastleggen(page, f"Kajak {STEMPEL}", "Kajak", eigenaar_index=2)
    boot_vastleggen(page, f"Clubboot {STEMPEL}", "Supboard")

    toewijzen(page, code, f"Kajak {STEMPEL}")
    expect(page.get_by_role("alert")).to_contain_text(f"Plaats {code} is niet geschikt voor een kajak")
    toewijzen(page, code, f"Clubboot {STEMPEL}")
    expect(page.get_by_role("alert")).to_contain_text("is een clubboot en hoort op een clubplaats")
    expect(page.get_by_role("heading", name="Deze plaats is vrij")).to_be_visible()
    expect(page.locator("section.log")).not_to_contain_text("plaats.toegewezen")
