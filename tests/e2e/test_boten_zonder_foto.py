"""Boten zonder foto (#315), de route voor een mens: kies in het menu onder Boten de lijst, zie een boot
zonder foto erop en een boot met foto niet, voeg via de pagina van de boot een foto toe en zie dat de boot
van de lijst is. Op 1100 en 360 pixels breed. De boten hebben geen plaats (geen rek nodig); de volgorde
staat in de unittests."""

from conftest import STEMPEL, menu_kiezen, menu_openen, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, png


def regel_van(page, boot):
    return page.locator("main > ul.bl-lijst > li").filter(has=page.get_by_role("link", name=boot, exact=True))


def test_boot_zonder_foto_staat_op_de_lijst_en_na_een_foto_niet_meer(page):
    wachtwoord_instellen(page, "zonderfoto")
    kaal, met = f"Kaal {STEMPEL}", f"Gefotografeerd {STEMPEL}"
    boot_vastleggen(page, kaal, "Kajak", eigenaar_index=2)
    boot_vastleggen(page, met, "Kajak", eigenaar_index=2, foto=png())

    # Het menu-item staat onder Boten, als laatste, zonder aantal.
    page.goto("/rekoverzicht")
    namen = menu_openen(page, "Boten").get_by_role("link").all_inner_texts()
    assert namen[-1] == "Boten zonder foto"
    menu_kiezen(page, "Boten", "Boten zonder foto")
    expect(page.get_by_role("heading", level=1)).to_have_text("Boten zonder foto")
    expect(page.locator("p.bl-aantal")).to_contain_text("zonder foto")
    expect(regel_van(page, kaal)).to_contain_text("geen plaats")
    expect(regel_van(page, kaal).locator("[data-label='Bootsoort']")).to_have_text("Kajak")
    expect(regel_van(page, met)).to_have_count(0)
    for breedte in (1100, 360):
        page.set_viewport_size({"width": breedte, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), breedte
    page.set_viewport_size({"width": 1100, "height": 900})

    # Een foto toevoegen op de pagina van de boot: daarna staat de boot niet meer op de lijst.
    aantal = int(page.locator("p.bl-aantal").inner_text().split()[0])
    regel_van(page, kaal).get_by_role("link", name=kaal, exact=True).click()
    page.get_by_text("Foto vervangen", exact=True).click()
    page.get_by_label("Nieuwe foto (JPEG, PNG of WebP)").set_input_files(
        {"name": "boot.png", "mimeType": "image/png", "buffer": png()})
    page.get_by_role("button", name="Foto opslaan").click()
    expect(page.get_by_role("img", name=f"Foto van {kaal}")).to_be_visible()
    page.goto("/boten-zonder-foto")
    expect(regel_van(page, kaal)).to_have_count(0)
    if aantal == 1:
        expect(page.get_by_text("Alle boten hebben een foto.")).to_be_visible()
    else:
        expect(page.locator("p.bl-aantal")).to_contain_text(f"{aantal - 1} ")
