"""Indeling, boot, toewijzen, log en openbare pagina (BLB-001, 005, 010, 012, 020, 025).

Elke test maakt eigen rekken, plaatsen en boten met de stempel van de run, zodat hij los en in
elke volgorde draait. De leden komen uit flask seed (draai.sh)."""

import os
import re
import struct
import zlib

from conftest import reknaam, uitloggen, wachtwoord_instellen
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


def sectie_van(page, rek):
    return page.locator("section.kaart", has=page.get_by_role("heading", name=rek, exact=True))


def rek_aanmaken(page, rek, vakken=((1, 1),), omschrijving=""):
    """Een rek met de vakken (verdieping, vak) aan in het raster van Nieuw rek, vanaf /indeling."""
    page.goto("/indeling")
    nieuw = page.locator("section.kaart", has=page.get_by_role("heading", name="Nieuw rek"))
    nieuw.get_by_label("Naam van het rek").fill(rek)
    nieuw.get_by_label("Omschrijving").fill(omschrijving)
    for verdieping, vak in vakken:
        nieuw.get_by_label(f"Verdieping {verdieping}, vak {vak}", exact=True).check()
    nieuw.get_by_role("button", name="Rek aanmaken").click()
    expect(page.get_by_text("Het rek is aangemaakt.")).to_be_visible()


def plaats_instellen(page, code, soorten, club=False):
    """Bootsoorten en clubplaats van een plaats; een nieuw vak heeft nog geen bootsoort."""
    page.goto("/indeling")
    page.get_by_role("link", name=code, exact=True).click()
    for soort in soorten:
        page.get_by_label(soort, exact=True).check()
    if club:
        page.get_by_label("Clubplaats (alleen voor clubboten)").check()
    page.get_by_role("button", name="Plaats opslaan").click()
    expect(page.get_by_text("De plaats is opgeslagen.")).to_be_visible()


def rek_met_plaats(page, rek, soorten, club=False):
    """Een rek met één plaats, <rek>/1/1, geschikt voor soorten; geeft de aanduiding. Eindigt op
    /indeling."""
    rek_aanmaken(page, rek)
    plaats_instellen(page, f"{rek}/1/1", soorten, club)
    page.goto("/indeling")
    return f"{rek}/1/1"


def rek_hernoemen(page, rek, nieuw):
    page.goto("/indeling")
    sectie = sectie_van(page, rek)
    sectie.get_by_text("Rek wijzigen of verwijderen").click()
    sectie.get_by_label("Naam", exact=True).fill(nieuw)
    sectie.get_by_role("button", name="Rek opslaan").click()
    expect(page.get_by_text("Het rek is opgeslagen.")).to_be_visible()


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
    rek, bootnaam = reknaam("i"), f"Boot {reknaam('i')}"
    code = rek_met_plaats(page, rek, ["Kajak"])
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2, foto=png())
    expect(page.get_by_role("img", name=f"Foto van {bootnaam}")).to_be_visible()

    toewijzen(page, code, bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    expect(page.locator("section.log")).to_contain_text("plaats.toegewezen")
    detail = page.url
    # BLB-043: de toewijzing staat alleen in het log van de bootmutaties, het nieuwe token (vlak
    # voor deze aanroep gemaakt door draai.sh) alleen in het technische log.
    token = os.environ["E2E_TOKEN_NIEUW_NAAM"]
    page.get_by_role("link", name="Log", exact=True).click()
    expect(page.locator("section.log")).to_contain_text(f"boot: {bootnaam}; plaats: {code}")
    expect(page.locator("section.log")).not_to_contain_text(token)
    page.get_by_role("link", name="Technisch log").click()
    expect(page.locator("section.log")).to_contain_text(token)
    expect(page.locator("section.log")).not_to_contain_text("plaats.toegewezen")
    page.goto(detail)
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
    rek = reknaam("r")
    code = rek_met_plaats(page, rek, ["Supboard"])
    boot_vastleggen(page, f"Kajak {rek}", "Kajak", eigenaar_index=2)
    boot_vastleggen(page, f"Clubboot {rek}", "Supboard")

    toewijzen(page, code, f"Kajak {rek}")
    expect(page.get_by_role("alert")).to_contain_text(f"Plaats {code} is niet geschikt voor een kajak")
    toewijzen(page, code, f"Clubboot {rek}")
    expect(page.get_by_role("alert")).to_contain_text("is een clubboot en hoort op een clubplaats")
    expect(page.get_by_role("heading", name="Deze plaats is vrij")).to_be_visible()
    expect(page.locator("section.log")).not_to_contain_text("plaats.toegewezen")


def test_plaats_wijzigen_vrijgeven_en_clubplaats(page):
    """BLB-002, 003 en 011 op één plaats, met de QR-link die blijft werken na een nieuwe reknaam
    (BLB-004 is vervallen: de aanduiding wijzigt alleen met de naam van het rek)."""
    wachtwoord_instellen(page, "plaatsbeheer")
    rek, nieuw, bootnaam = reknaam("p"), reknaam("q"), f"Plaatsboot {reknaam('p')}"
    code = rek_met_plaats(page, rek, ["Kajak", "Surfski"])
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2)
    toewijzen(page, code, bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    openbare_link = page.locator("#openbare-link").get_attribute("href")
    expect(page.get_by_label("Plaatscode")).to_have_count(0)  # de aanduiding is niet los te wijzigen

    page.get_by_label("Kajak", exact=True).uncheck()
    page.get_by_role("button", name="Plaats opslaan").click()
    expect(page.get_by_role("alert")).to_contain_text(f"ligt {bootnaam}, een kajak")

    rek_hernoemen(page, rek, nieuw)
    code = f"{nieuw}/1/1"
    page.get_by_role("link", name=code, exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_have_text(f"Plaats {code}")
    page.goto(openbare_link)
    expect(page.get_by_role("heading", level=1)).to_have_text(f"Plaats {code}")
    expect(page.get_by_text(bootnaam)).to_be_visible()
    page.go_back()

    page.get_by_label("Clubplaats (alleen voor clubboten)").check()
    page.get_by_role("button", name="Plaats opslaan").click()
    expect(page.get_by_role("alert")).to_contain_text("Geef de plaats eerst vrij")

    page.get_by_role("button", name=f"Plaats {code} vrijgeven").click()
    expect(page.get_by_text("De plaats is vrijgegeven.")).to_be_visible()
    expect(page.get_by_role("heading", name="Deze plaats is vrij")).to_be_visible()
    expect(page.locator("section.log")).to_contain_text("plaats.vrijgegeven")

    page.get_by_label("Clubplaats (alleen voor clubboten)").check()
    page.get_by_role("button", name="Plaats opslaan").click()
    expect(page.get_by_text("De plaats is opgeslagen.")).to_be_visible()
    toewijzen(page, code, bootnaam)
    expect(page.get_by_role("alert")).to_contain_text("is een clubplaats en alleen voor clubboten")


def test_boot_wijzigen_en_weigeren_met_log(page):
    """BLB-005, issue #39: naam en bootsoort wijzigen, een bootsoort die de plaats niet past
    weigeren, en het log van de bootmutaties onder de boot."""
    wachtwoord_instellen(page, "bootwijzigen")
    rek = reknaam("b")
    bootnaam, nieuw = f"Wijzigboot {rek}", f"Nieuwe naam {rek}"
    code = rek_met_plaats(page, rek, ["Kajak"])
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2)
    toewijzen(page, code, bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    page.get_by_role("link", name=bootnaam).click()

    formulier = page.locator("section.kaart", has=page.get_by_role("heading", name="Boot wijzigen"))
    formulier.get_by_label("Bootsoort").select_option(label="C11")
    formulier.get_by_role("button", name="Boot opslaan").click()
    expect(page.get_by_role("alert")).to_contain_text(f"Plaats {code} is niet geschikt voor een c11")
    expect(page.locator("section.log")).not_to_contain_text("boot.gewijzigd")

    formulier.get_by_label("Naam van de boot").fill(nieuw)
    formulier.get_by_role("button", name="Boot opslaan").click()
    expect(page.get_by_text("De boot is opgeslagen.")).to_be_visible()
    expect(page.get_by_role("heading", level=1)).to_have_text(nieuw)
    expect(page.locator("section.log")).to_contain_text(f"naam: ['{bootnaam}', '{nieuw}']")
    expect(page.locator("section.log")).to_contain_text("boot.gewijzigd")
