"""Overloop op 360 px (#270, #169): Boot met het blok Wijzigen open, Indeling en Rekoverzicht blijven
binnen het venster. De plaatsen hebben bootsoort Supboard, die geen plaatje heeft (ADR-002): het vak toont dan
tekst en een dj-sr-only, die zonder bevattende blok de pagina oprekt."""

from conftest import blok_openen, reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, rek_aanmaken, toewijzen


def test_pagina_blijft_op_360_px_binnen_het_venster(page):
    wachtwoord_instellen(page, "overloop")
    rek = reknaam("a")
    bootnaam = f"Zwarte Parel van het Merengebied {rek}"  # de knop Boot ... verwijderen is dan breder dan het venster
    # Beginwaarden: een rek met tien plaatsen van bootsoort Supboard op één verdieping, de eerste bezet, de rest vrij.
    # Vanaf ongeveer het vijfde vak ligt een cel buiten een venster van 360 px, waar een dj-sr-only de pagina oprekt.
    rek_aanmaken(page, rek, vakken=[(1, n) for n in range(1, 11)], soorten={1: "Supboard"})
    boot_vastleggen(page, bootnaam, "Supboard", eigenaar_index=2)
    toewijzen(page, f"{rek}/1/1", bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()

    page.set_viewport_size({"width": 360, "height": 740})
    te_breed = []
    for pad in ("/indeling", "/rekoverzicht", None):
        if pad:
            page.goto(pad)
        else:
            page.goto("/boten")
            page.get_by_role("link", name=bootnaam, exact=True).click()
            blok_openen(page, "Boot wijzigen")
            expect(page.locator("details[open] > summary", has_text="Boot wijzigen")).to_have_count(1)
        if not page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"):
            te_breed.append(pad or "boot")
    assert not te_breed, te_breed
