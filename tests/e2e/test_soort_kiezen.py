"""Bezetting importeren (issue #202), de route voor een mens: bij een onbekende bootsoort de juiste soort
kiezen (één lijst, of twee lijsten bij een regel met ook een eigenaar die niet te koppelen is), opslaan,
importeren en controleren dat de boot de gekozen soort heeft. Op 1100 en 360 pixels breed, met een
Tab-run door de cel Keuze. Eigen bestand."""

import re

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_bezetting_csv import KOP, leden_uit_de_lijst, lid_kiezen_bij_regel, regel, uploaden
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
    assert opties(een) == ["Geen keuze", "Kajak", "Surfski"]  # de soorten van plaats 1, zonder Regel overslaan
    groep = page.get_by_role("group", name="Keuze voor regel 3")
    soort, eigenaar = groep.get_by_label("Bootsoort"), groep.get_by_label("Eigenaar", exact=True)
    assert opties(soort) == ["Geen keuze", "Kajak"]  # plaats 2 laat alleen kajak toe
    expect(eigenaar).to_have_value(f"Onbekend {rek}")  # het zoekveld begint met de naam uit het bestand
    expect(page.get_by_role("button", name="Bezetting importeren", exact=True)).to_be_disabled()
    for breedte in (1100, 360):
        page.set_viewport_size({"width": breedte, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), breedte
        expect(groep).to_be_visible()
        # Tab: van de lijst van regel 2 naar zijn vakje, dan Bootsoort, Eigenaar, het vakje van regel 3,
        # de lijst van regel 4, zijn vakje, Zoeken en Keuzes opslaan.
        een.focus()
        for veld in (regel(page, fuut).get_by_label("Regel overslaan"), soort, eigenaar,
                     groep.get_by_label("Regel overslaan"), page.get_by_label("Keuze voor regel 4", exact=True),
                     regel(page, reiger).get_by_label("Regel overslaan"),
                     page.locator('form[action="/bezetting/import/koppelen"]').get_by_role("button", name="Zoeken", exact=True),
                     page.get_by_role("button", name="Keuzes opslaan")):
            page.keyboard.press("Tab")
            expect(veld).to_be_focused()

    # Issue #218 en #295: regel 4 overslaan met het vakje, opslaan: alleen het aangevinkte vakje blijft; uitvinken
    # brengt de lijst met de soorten van de plaats terug en een soort kiezen is een keer opslaan.
    regel(page, reiger).get_by_label("Regel overslaan").check()
    page.get_by_role("button", name="Keuzes opslaan").click()
    expect(regel(page, reiger)).to_contain_text("overgeslagen")
    expect(page.get_by_label("Keuze voor regel 4", exact=True)).to_have_count(0)
    regel(page, reiger).get_by_label("Regel overslaan").uncheck()
    page.get_by_role("button", name="Keuzes opslaan").click()
    assert opties(page.get_by_label("Keuze voor regel 4", exact=True)) == ["Geen keuze", "Kajak"]
    page.get_by_label("Keuze voor regel 4", exact=True).select_option(label="Kajak")
    page.get_by_role("button", name="Keuzes opslaan").click()
    expect(regel(page, reiger)).to_contain_text("nieuwe boot")

    # De juiste soort kiezen en opslaan: beide regels zijn in orde; beide keuzes blijven wijzigbaar.
    een.select_option(label="Surfski")
    soort.select_option(label="Kajak")
    lid_kiezen_bij_regel(page, meeuw, "Eigenaar", nr1)
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

