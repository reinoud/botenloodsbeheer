"""Zoeken vanuit de kop (#154), de route voor een mens: een term met twee treffers geeft de lijst,
een deel van een bootnaam met één treffer opent de boot, op 360 en 1100 pixels breed. Eén
inlogverzoek. Elk bestand van de run gebruikt een eigen rek, dus de rekletter is hier niet gedeeld."""

import re

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, rek_aanmaken, toewijzen

KOP_LABEL = "Zoeken naar plaats, boot of eigenaar"


def zoeken_in_de_kop(page, term):
    """Typt de term in het zoekveld van de kop en kiest de knop Zoeken van de kop, niet die van main."""
    kop = page.locator("header.bl-kop")
    veld = kop.get_by_label(KOP_LABEL)
    veld.fill(term)
    kop.get_by_role("button", name="Zoeken").click()


def test_zoeken_vanuit_de_kop_geeft_een_lijst_of_opent_de_boot(page):
    wachtwoord_instellen(page, "zoeken")
    rek = reknaam("j")
    aal, zee = f"Aal {rek}", f"Zee {rek}"
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2)), soorten={1: "Kajak"})
    boot_vastleggen(page, aal, "Kajak", eigenaar_index=2)
    toewijzen(page, f"{rek}/1/1", aal)
    boot_vastleggen(page, zee, "Kajak", eigenaar_index=None)
    toewijzen(page, f"{rek}/1/2", zee)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()

    for breedte in (360, 1100):
        page.set_viewport_size({"width": breedte, "height": 900})
        page.goto("/rekoverzicht")
        veld = page.locator("header.bl-kop").get_by_label(KOP_LABEL)
        expect(veld).to_have_attribute("placeholder", "Plaats, boot of eigenaar")
        # Het veld, de knop en op een telefoon ook de knop Menu passen in de kop; het veld blijft bruikbaar breed.
        kop = page.locator("header.bl-kop")
        menu = (kop.locator("summary.dj-menu__button"),) if breedte == 360 else ()  # breed: menu open, knop weg
        for element in (veld, kop.get_by_role("button", name="Zoeken"), *menu):
            doos = element.bounding_box()
            assert doos["x"] >= 0 and doos["x"] + doos["width"] <= breedte, (breedte, doos)
        # De preview van BV-75 (designsystem b0f0f1c) meet op 360 px 97 px; marge voor lettertype en afronding.
        assert veld.bounding_box()["width"] >= 90, breedte

        # Twee treffers: de lijst, met het aantal, de plaatsen en de term nog in het kopveld.
        zoeken_in_de_kop(page, rek)
        expect(page).to_have_url(re.compile(r"/zoeken\?q=" + rek + "$"))
        expect(page.get_by_role("heading", level=1)).to_have_text("Zoekresultaten")
        expect(page.locator("main > .bl-aantal")).to_have_text(f'2 treffers voor "{rek}"')
        items = page.locator("main > ul.bl-lijst > li")
        expect(items).to_have_count(2)
        expect(items.nth(0).locator(".bl-item__titel")).to_have_text(aal)
        expect(items.nth(0).locator(".bl-plaatslink")).to_have_text(f"{rek}/1/1")
        expect(items.nth(1).locator(".bl-item__titel")).to_have_text(zee)
        expect(items.nth(1).locator(".bl-plaatslink")).to_have_text(f"{rek}/1/2")
        expect(items.nth(0).locator("[data-label=Eigenaar]")).to_contain_text("(")  # naam (lidnummer)
        expect(items.nth(1).locator("[data-label=Eigenaar]")).to_have_text("clubboot")
        expect(page.locator("header.bl-kop").get_by_label(KOP_LABEL)).to_have_value(rek)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), breedte

        # Eén treffer: een deel van een bootnaam opent de boot, met de juiste plaats.
        zoeken_in_de_kop(page, f"ee {rek}")
        expect(page).to_have_url(re.compile(r"/boten/\d+$"))
        expect(page.get_by_role("heading", level=1)).to_have_text(zee)
        expect(page.locator("dl.bl-feiten").get_by_role("link", name=f"{rek}/1/2", exact=True)).to_be_visible()

        # Te kort: geen zoekopdracht, de melding.
        zoeken_in_de_kop(page, " x ")
        expect(page.locator("main .ds-notice [role=status]")).to_have_text("Typ minstens 2 tekens.")
