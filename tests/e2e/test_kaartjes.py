"""Kaartjes met QR-code (BLB-021, ADR-011): kiezen, printen in Chromium en Firefox, en de link
uit de QR-code als bezoeker openen. Dat de QR-code die link codeert, toetst
tests/unit/test_kaartjes.py; dit image heeft geen QR-lezer.

Eigen rek en plaatsen met de stempel van de run; het lid komt uit de import (draai.sh)."""

import math
import re

from conftest import reknaam, uitloggen, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, plaats_instellen, rek_aanmaken, rek_hernoemen, toewijzen

MM = 96 / 25.4  # CSS-pixels per millimeter


def kaartje(page, code):
    return page.locator("section.kaartje", has=page.locator(
        ".kaartje-code", has_text=re.compile(f"^{re.escape(code)}$")))


def kiezen(page, *labels):
    page.goto("/kaartjes")
    for label in labels:
        page.get_by_label(label, exact=True).check()
    page.get_by_role("button", name="Kaartjes maken").click()
    page.wait_for_load_state()  # alle plaatsen is een grote pagina; tel pas als hij er helemaal is


def past_op_a4(page):
    """In printweergave: geen kopbalk, en elk blad binnen A4 min 10 mm marge (190 x 277 mm)."""
    page.emulate_media(media="print")
    expect(page.locator("header.kop")).to_be_hidden()
    for blad in page.locator(".blad").all():
        vak = blad.bounding_box()
        assert vak["width"] <= 190 * MM + 1 and vak["height"] <= 277 * MM + 1, vak
        for k in blad.locator(".kaartje").all():
            binnen = k.bounding_box()
            assert binnen["x"] + binnen["width"] <= vak["x"] + vak["width"] + 1
            assert binnen["y"] + binnen["height"] <= vak["y"] + vak["height"] + 1
    page.emulate_media(media="no-override")  # met "screen" zou page.pdf() ook schermstijl gebruiken


def test_kaartjes_kiezen_printen_en_qr_openen(page, playwright, browser, base_url):
    wachtwoord_instellen(page, "kaartjes")
    vereniging = page.locator(".kop-naam").inner_text()
    rek, nieuw, bootnaam = reknaam("k"), reknaam("m"), f"Kaartboot {reknaam('k')}"
    omschrijving = "Proefstelling links bij de deur, tot 60 tekens lang gehouden"
    bezet, vrij, club = f"{rek}/1/1", f"{rek}/1/2", f"{rek}/1/3"
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2), (1, 3)), omschrijving=omschrijving)
    plaats_instellen(page, bezet, ["Kajak"])
    plaats_instellen(page, vrij, ["Kajak"])
    plaats_instellen(page, club, ["Kajak"], club=True)
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2)
    toewijzen(page, bezet, bootnaam)
    prive = {veld: page.locator(f"[data-veld={veld}]").inner_text()
             for veld in ("naam", "lidnummer", "adres", "telefoon", "email")}
    openbare_link = page.locator("#openbare-link").get_attribute("href")

    # Zonder keuze: terug met een melding.
    kiezen(page)
    expect(page.get_by_role("alert")).to_have_text(
        "Kies een of meer plaatsen, een rek of alle plaatsen.")

    # Eén plaats: logo, code, eigenaar en QR-code; geen andere persoonsgegevens.
    kiezen(page, bezet)
    expect(page.locator("section.kaartje")).to_have_count(1)
    een = kaartje(page, bezet)
    expect(een.locator("img.kaartje-logo")).to_be_visible()
    expect(een.locator(".kaartje-eigenaar")).to_have_text(prive["naam"])
    expect(een.locator(".kaartje-omschrijving")).to_have_text(omschrijving)  # BLB-021
    expect(een.get_by_role("img", name=f"QR-code naar de openbare pagina van {bezet}")).to_be_visible()
    html = page.content()
    for veld in ("lidnummer", "adres", "telefoon", "email"):
        assert prive[veld] not in html, veld
    assert bootnaam not in html
    qr = een.locator("svg.qr-kaartje path").get_attribute("d")

    # Per rek: vrije plaats en clubplaats; past op A4 in Chromium.
    kiezen(page, f"Heel {rek}")
    expect(page.locator(".kaartje-code")).to_have_text([bezet, vrij, club])
    expect(kaartje(page, vrij).locator(".kaartje-eigenaar")).to_have_text("vrij")
    expect(kaartje(page, club).locator(".kaartje-eigenaar")).to_have_text(vereniging)
    past_op_a4(page)
    per_rek = page.url

    # Dezelfde pagina in Firefox, met de sessie van deze test (ADR-011).
    firefox = playwright.firefox.launch()
    try:
        ff = firefox.new_context(base_url=base_url, storage_state=page.context.storage_state())
        ff_page = ff.new_page()
        ff_page.goto(per_rek)
        expect(ff_page.locator(".kaartje-code")).to_have_text([bezet, vrij, club])
        past_op_a4(ff_page)
    finally:
        firefox.close()

    # Alle plaatsen: acht per A4, dus zoveel pdf-pagina's als bladen (Chromium).
    kiezen(page, "Alle plaatsen")
    aantal = page.locator("section.kaartje").count()
    assert aantal >= 3
    pdf = page.pdf(prefer_css_page_size=True)
    assert len(re.findall(rb"/Type\s*/Page\b", pdf)) == math.ceil(aantal / 8)

    # De naam van het rek wijzigen: zelfde QR-code, nieuwe aanduiding op het kaartje.
    rek_hernoemen(page, rek, nieuw)
    nieuw = f"{nieuw}/1/1"
    kiezen(page, nieuw)
    expect(kaartje(page, nieuw).locator("svg.qr-kaartje path")).to_have_attribute("d", qr)

    # De link uit de QR-code, als bezoeker zonder inloggen.
    uitloggen(page)
    page.goto("/kaartjes")
    expect(page).to_have_url(re.compile(r"/inloggen$"))
    bezoeker = browser.new_page(base_url=base_url)
    bezoeker.goto(openbare_link)
    expect(bezoeker.get_by_role("heading", level=1)).to_have_text(f"Plaats {nieuw}")
    expect(bezoeker.get_by_text(prive["naam"], exact=True)).to_be_visible()
    bezoeker.close()
