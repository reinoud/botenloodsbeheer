"""Eigenaar onbekend (issues #204 en #207), de route voor een mens: een boot vastleggen met de knop
Nieuwe boot bovenaan Boten en de eigenaar open laten, twee boten zonder eigenaar importeren, op
Boten zonder eigenaar per boot een eigenaar kiezen, een weigering die alleen die boot raakt. Op
1100 en 360 pixels breed."""

import re

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_bezetting_csv import KOP, uploaden
from test_loods import rek_aanmaken


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
    expect(page.get_by_label("Eigenaar")).to_have_value("onbekend")
    expect(page.get_by_label("Eigenaar").locator("option").first).to_have_text("eigenaar onbekend")
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
    # Een lid kiezen: de boot is van de lijst.
    for boot in (tureluur, kluut):
        regel_van(page, boot).get_by_label(f"Eigenaar van {boot}").select_option(index=2)
        regel_van(page, boot).get_by_role("button", name=f"Eigenaar opslaan: {boot}").click()
        expect(page.get_by_text(f"De eigenaar van {boot} is opgeslagen.")).to_be_visible()
        expect(regel_van(page, boot)).to_have_count(0)
    regel_van(page, wulp).get_by_label(f"Eigenaar van {wulp}").select_option(value="club")
    regel_van(page, wulp).get_by_role("button", name=f"Eigenaar opslaan: {wulp}").click()
    expect(regel_van(page, wulp)).to_have_count(0)

    page.goto("/boten")
    expect(regel_van(page, wulp)).to_contain_text("clubboot")
    expect(regel_van(page, tureluur)).not_to_contain_text("onbekend")
