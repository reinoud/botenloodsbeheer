"""Bezetting importeren (issue #202), de route voor een mens: bij een onbekende bootsoort de juiste soort
kiezen (één lijst, of twee lijsten bij een regel met ook een eigenaar die niet te koppelen is), opslaan,
importeren en controleren dat de boot de gekozen soort heeft. Op 1100 en 360 pixels breed, met een
Tab-run door de cel Keuze. Eigen bestand."""

import re

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_bezetting_csv import KOP, leden_uit_de_lijst, regel, uploaden
from test_loods import plaats_instellen, rek_aanmaken


def opties(lijst):
    return lijst.locator("option").all_text_contents()


def test_bij_een_onbekende_bootsoort_de_juiste_soort_kiezen_en_importeren(page):
    wachtwoord_instellen(page, "bezettingsoort")
    rek = reknaam("n")
    (naam1, nr1), _tweede = leden_uit_de_lijst(page)
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2), (1, 3)), soorten={1: "Kajak"})
    plaats_instellen(page, f"{rek}/1/1", ["Surfski"])  # plaats 1 laat kajak en surfski toe, plaats 2 alleen kajak
    fuut, meeuw, reiger = f"Fuut {rek}", f"Meeuw {rek}", f"Reiger {rek}"

    # Regel 2: een verkeerd geschreven soort, de eigenaar is te vinden: één lijst. Regel 3: ook een eigenaar die
    # niet te koppelen is: twee lijsten onder elkaar in een groep.
    uploaden(page, "\r\n".join([KOP, f"{rek}/1/1;{fuut};Kayak;{naam1};{nr1}",
                                f"{rek}/1/2;{meeuw};Surfsky;Onbekend {rek};",
                                f"{rek}/1/3;{reiger};Kayak;{naam1};{nr1}"]) + "\r\n")
    expect(regel(page, fuut)).to_contain_text("De bootsoort Kayak bestaat niet of is dubbelzinnig, kies hem in de lijst.")
    een = page.get_by_label("Keuze voor regel 2", exact=True)
    expect(een).to_be_visible()
    assert opties(een) == ["Geen keuze", "Regel overslaan", "Kajak", "Surfski"]  # de soorten van plaats 1
    groep = page.get_by_role("group", name="Keuze voor regel 3")
    soort, eigenaar = groep.get_by_label("Bootsoort"), groep.get_by_label("Eigenaar")
    assert opties(soort) == ["Geen keuze", "Regel overslaan", "Kajak"]  # plaats 2 laat alleen kajak toe
    assert "Regel overslaan" not in opties(eigenaar) and f"{naam1} ({nr1})" in opties(eigenaar)
    expect(page.get_by_role("button", name="Bezetting importeren", exact=True)).to_be_disabled()
    for breedte in (1100, 360):
        page.set_viewport_size({"width": breedte, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), breedte
        expect(groep).to_be_visible()
        # Tab: van de lijst van regel 2 naar Bootsoort, Eigenaar, de lijst van regel 4 en dan Keuzes opslaan.
        een.focus()
        page.keyboard.press("Tab")
        expect(soort).to_be_focused()
        page.keyboard.press("Tab")
        expect(eigenaar).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_label("Keuze voor regel 4", exact=True)).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.get_by_role("button", name="Keuzes opslaan")).to_be_focused()

    # Issue #218: regel 4 overslaan, opslaan: de soorten van de plaats blijven in de lijst en een soort kiezen
    # (direct, zonder eerst Geen keuze) is een keer opslaan.
    vier = page.get_by_label("Keuze voor regel 4", exact=True)
    vier.select_option(label="Regel overslaan")
    page.get_by_role("button", name="Keuzes opslaan").click()
    expect(regel(page, reiger)).to_contain_text("overgeslagen")
    assert opties(page.get_by_label("Keuze voor regel 4", exact=True)) == ["Geen keuze", "Regel overslaan", "Kajak"]
    page.get_by_label("Keuze voor regel 4", exact=True).select_option(label="Kajak")
    page.get_by_role("button", name="Keuzes opslaan").click()
    expect(regel(page, reiger)).to_contain_text("nieuwe boot")

    # De juiste soort kiezen en opslaan: beide regels zijn in orde; beide keuzes blijven wijzigbaar.
    een.select_option(label="Surfski")
    soort.select_option(label="Kajak")
    eigenaar.select_option(label=f"{naam1} ({nr1})")
    page.get_by_role("button", name="Keuzes opslaan").click()
    expect(page.get_by_text("De keuzes zijn opgeslagen.")).to_be_visible()
    expect(regel(page, fuut)).to_contain_text("nieuwe boot")
    expect(regel(page, meeuw)).to_contain_text("nieuwe boot")
    expect(page.get_by_label("Keuze voor regel 2", exact=True)).to_have_value(re.compile(r"\d+"))
    expect(page.get_by_role("group", name="Keuze voor regel 3").get_by_label("Bootsoort")).not_to_have_value("")
    page.get_by_role("button", name="Bezetting importeren", exact=True).click()
    expect(page.get_by_text("De bezetting is geïmporteerd. Nieuwe boten: 3")).to_be_visible()

    # De boten hebben de gekozen soort.
    for boot, gekozen in ((fuut, "Surfski"), (meeuw, "Kajak"), (reiger, "Kajak")):
        page.goto("/boten")
        page.get_by_role("link", name=boot, exact=True).click()
        expect(page.locator("dl.bl-feiten > div").filter(has_text="Bootsoort")).to_contain_text(gekozen)

