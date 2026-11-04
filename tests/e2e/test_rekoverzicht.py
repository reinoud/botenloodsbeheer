"""Rekoverzicht (issue #87): per plaats één vak met het verwachte plaatje en de alt-tekst."""

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, plaats_instellen, rek_aanmaken, sectie_van, toewijzen


def test_rekoverzicht_toont_per_plaats_een_plaatje_met_alt(page):
    wachtwoord_instellen(page, "rekoverzicht")
    rek, bootnaam = reknaam("o"), f"Boot {reknaam('o')}"
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2), (2, 1), (2, 2)),
                 soorten={1: "Kajak", 2: "Surfski"})
    plaats_instellen(page, f"{rek}/1/2", ["Kajak"], club=True)
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2)
    toewijzen(page, f"{rek}/1/1", bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()

    page.get_by_role("link", name="Rekoverzicht", exact=True).click()
    sectie = sectie_van(page, rek)
    expect(sectie.locator("a.rek-vak")).to_have_count(4)
    verwacht = {
        f"Plaats {rek}/1/1, Kajak, bezet": "kajak-bezet.jpg",
        f"Plaats {rek}/1/2, Kajak, clubplaats, leeg": "kajak-vrij.jpg",
        f"Plaats {rek}/2/1, Surfski, vrij": "surfski-vrij.jpg",
        f"Plaats {rek}/2/2, Surfski, vrij": "surfski-vrij.jpg",
    }
    for alt, bestand in verwacht.items():
        plaatje = sectie.get_by_role("img", name=alt, exact=True)
        expect(plaatje).to_have_attribute("src", f"/static/boten/{bestand}")
        expect(plaatje).to_be_visible()  # het bestand bestaat en laadt
        assert plaatje.evaluate("i => i.naturalWidth") > 0, alt
    expect(sectie.locator("a.rek-vak-club")).to_have_count(1)
    expect(sectie.locator("a.rek-vak-club").get_by_role("img")).to_have_attribute(
        "alt", f"Plaats {rek}/1/2, Kajak, clubplaats, leeg")

    sectie.get_by_role("link", name=f"Plaats {rek}/2/1, Surfski, vrij").click()
    expect(page.get_by_role("heading", level=1)).to_have_text(f"Plaats {rek}/2/1")
