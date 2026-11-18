"""Eigenaar onbekend (issues #204 en #207), de route voor een mens: een boot vastleggen met de knop
Nieuwe boot bovenaan Boten en de eigenaar open laten, twee boten zonder eigenaar importeren, op
naar een boot klikken en daar een eigenaar kiezen (#321). Op
1100 en 360 pixels breed. Daarna een boot met een eigenaar weer onbekend maken (#233)."""

import re

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_bezetting_csv import KOP, uploaden
from test_loods import (
    boot_vastleggen,
    kiesbare_leden,
    lid_zoeken_en_kiezen,
    plaats_instellen,
    rek_aanmaken,
    toewijzen,
)


def regel_van(page, boot):
    return page.locator("main > ul.bl-lijst > li").filter(has=page.get_by_role("link", name=boot, exact=True))


def zonder_scroll(page):
    for breedte in (1100, 360):
        page.set_viewport_size({"width": breedte, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), breedte


def test_eigenaar_onbekend_vastleggen_importeren_en_een_eigenaar_kiezen(page):
    wachtwoord_instellen(page, "eigenaaronbekend")
    rek = reknaam("d")
    wulp, tureluur, kluut = f"Wulp {rek}", f"Tureluur {rek}", f"Kluut {rek}"
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2)), soorten={1: "Kajak"})

    # #207: de knop Nieuwe boot staat bovenaan, dicht; de eigenaar begint op eigenaar onbekend.
    page.goto("/boten")
    nieuw = page.locator("main > details.bl-nieuw")
    expect(nieuw).not_to_have_attribute("open", "")
    assert page.evaluate("document.querySelector('#nieuw-kop').getBoundingClientRect().top "
                         "< document.querySelector('#boten-zoek').getBoundingClientRect().top")
    page.locator("#nieuw-kop").click()
    page.get_by_label("Naam van de boot").fill(wulp)
    page.get_by_label("Bootsoort").select_option(label="Kajak")
    eigenaar = page.get_by_label("Eigenaar", exact=True)  # exact: het zoekveld in de kop noemt ook de eigenaar
    expect(eigenaar).to_have_value("")  # leeg is eigenaar onbekend (BV-85)
    expect(eigenaar).not_to_have_attribute("required", "")
    expect(page.get_by_text("Laat de eigenaar open als die nog niet bekend is.")).to_be_visible()
    page.get_by_role("button", name="Boot vastleggen").click()
    expect(page.get_by_text("De boot is vastgelegd.")).to_be_visible()
    expect(page.locator("dl.bl-feiten dd").nth(1)).to_have_text("onbekend")

    # #204: een import met lege eigenaar maakt boten met een onbekende eigenaar, geen clubboten.
    uploaden(page, "\r\n".join([KOP, f"{rek}/1/1;{tureluur};Kajak;;", f"{rek}/1/2;{kluut};Kajak;;"]) + "\r\n")
    page.get_by_role("button", name="Bezetting importeren", exact=True).click()
    expect(page.get_by_text("De bezetting is geïmporteerd.")).to_be_visible()

    page.goto("/boten")
    expect(regel_van(page, tureluur)).to_contain_text("eigenaar onbekend")
    expect(page.get_by_role("link", name=re.compile(r"^Boten zonder eigenaar \d+$"))).to_have_count(1)
    page.get_by_role("link", name=re.compile(r"^Boten zonder eigenaar")).evaluate("e => e.click()")
    expect(page.get_by_role("heading", level=1)).to_have_text("Boten zonder eigenaar")
    for boot, plaats in ((tureluur, f"{rek}/1/1"), (kluut, f"{rek}/1/2"), (wulp, "geen plaats")):
        expect(regel_van(page, boot)).to_contain_text(plaats)
    zonder_scroll(page)

    page.set_viewport_size({"width": 1100, "height": 900})
    # #321: geen keuze op de lijst; klik op de boot en kies de eigenaar bij Boot wijzigen. De boot is van de lijst.
    expect(page.get_by_text("Klik op de boot om een eigenaar toe te kennen.")).to_be_visible()
    expect(page.locator("main form, main input, main button")).to_have_count(0)
    (_naam, nummer), *_ = kiesbare_leden(page, 1)
    for boot, keuze in ((tureluur, nummer), (kluut, nummer), (wulp, "clubboot")):
        page.goto("/boten/zonder-eigenaar")
        page.get_by_role("link", name=boot, exact=True).click()
        expect(page.get_by_role("heading", level=1)).to_have_text(boot)
        page.get_by_text("Boot wijzigen of verwijderen", exact=True).click()
        formulier = page.locator("section.kaart", has=page.get_by_role("heading", name="Boot wijzigen"))
        lid_zoeken_en_kiezen(formulier.get_by_label("Eigenaar", exact=True),
                             formulier.get_by_role("button", name="Zoeken", exact=True), keuze)
        formulier.get_by_role("button", name="Boot opslaan").click()
        expect(page.get_by_text("De boot is opgeslagen.")).to_be_visible()
        page.goto("/boten/zonder-eigenaar")
        expect(regel_van(page, boot)).to_have_count(0)

    page.goto("/boten")
    expect(regel_van(page, wulp)).to_contain_text("clubboot")
    expect(regel_van(page, tureluur)).not_to_contain_text("onbekend")


def eigenaar_leegmaken(page, boot):
    page.goto("/boten")
    page.get_by_role("link", name=boot, exact=True).click()
    page.get_by_text("Boot wijzigen of verwijderen", exact=True).click()
    formulier = page.locator("section.kaart", has=page.get_by_role("heading", name="Boot wijzigen"))
    formulier.get_by_label("Eigenaar", exact=True).fill("")
    formulier.get_by_role("button", name="Boot opslaan").click()


def test_een_boot_van_een_lid_wordt_niet_onbekend_en_een_clubboot_eerst_van_de_clubplaats(page):
    wachtwoord_instellen(page, "weeronbekend")
    rek = reknaam("e")
    lidboot, clubboot = f"Lidboot {rek}", f"Clubboot {rek}"
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2)), soorten={1: "Kajak"})
    plaats_instellen(page, f"{rek}/1/2", [], club=True)
    boot_vastleggen(page, lidboot, "Kajak", eigenaar_index=2)
    boot_vastleggen(page, clubboot, "Kajak")
    toewijzen(page, f"{rek}/1/1", lidboot)
    toewijzen(page, f"{rek}/1/2", clubboot)

    # Unhappy (besluit 2026-11-17, BV-72 4A): een leeg veld Eigenaar bij een boot van een lid geeft een foutregel
    # bij het veld; de boot blijft van het lid. Het veld toont de huidige eigenaar tot je het leegmaakt.
    page.goto("/boten")
    page.get_by_role("link", name=lidboot, exact=True).click()
    page.get_by_text("Boot wijzigen of verwijderen", exact=True).click()
    expect(page.get_by_label("Eigenaar", exact=True)).not_to_have_value("")
    eigenaar_leegmaken(page, lidboot)
    veld = page.get_by_label("Eigenaar", exact=True)
    expect(veld).to_have_attribute("aria-invalid", "true")
    expect(page.get_by_text("Vul een eigenaar in. Een boot van een lid of oud-lid kan niet zonder eigenaar.")).to_be_visible()
    expect(page.locator("dl.bl-feiten dd").nth(1)).not_to_have_text("onbekend")
    page.goto("/boten/zonder-eigenaar")
    expect(regel_van(page, lidboot)).to_have_count(0)

    # Een clubboot op een clubplaats blijft clubboot, met een melding. Mutant: de voorwaarde
    # `clubboot != oude_club` in boot_wijzigen weg valt op de melding (de boot wordt dan onbekend).
    eigenaar_leegmaken(page, clubboot)
    expect(page.get_by_role("alert")).to_contain_text(f"Plaats {rek}/1/2 is een clubplaats en alleen voor clubboten")
    expect(page.locator("dl.bl-feiten dd").nth(1)).to_contain_text("(clubboot)")
    page.goto("/boten/zonder-eigenaar")
    expect(regel_van(page, clubboot)).to_have_count(0)

    # Na het vrijgeven van de plaats mag een clubboot wel onbekend worden (#233).
    page.goto("/indeling")
    page.get_by_role("link", name=f"{rek}/1/2", exact=True).click()
    page.get_by_role("button", name=f"Plaats {rek}/1/2 vrijgeven").click()
    expect(page.get_by_text("De plaats is vrijgegeven.")).to_be_visible()
    eigenaar_leegmaken(page, clubboot)
    expect(page.get_by_text("De boot is opgeslagen.")).to_be_visible()
    expect(page.locator("dl.bl-feiten dd").nth(1)).to_have_text("onbekend")
