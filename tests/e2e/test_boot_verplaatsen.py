"""Boot verplaatsen vanaf het scherm Boot (#206, ontwerp 5B): een dicht blok met een lege keuzelijst,
open na een weigering, en na Verplaats ligt de boot elders. Controle op 360 en 1100 px."""

from conftest import blok_openen, reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, rek_aanmaken, toewijzen


def boot_openen(page, bootnaam):
    page.goto("/boten")
    page.get_by_role("link", name=bootnaam, exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_have_text(bootnaam)


def past_in_de_kaart(page, kop):
    """De kaart van een uitklapblok past op de pagina en alles erin ligt binnen de kaart."""
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    kaart = page.locator("section.kaart", has=page.locator(f"summary#{kop}"))
    rand = kaart.bounding_box()["x"] + kaart.bounding_box()["width"]
    for el in kaart.locator("details[open] :is(select, input, button, label, h2)").all():
        doos = el.bounding_box()
        if doos is None:  # verborgen veld (csrf)
            continue
        assert doos["x"] + doos["width"] <= rand + 0.5, (kop, el.evaluate("e => e.outerHTML")[:80])


def test_boot_verplaatsen(page):
    wachtwoord_instellen(page, "bootverplaatsen")
    rek = reknaam("g")
    bootnaam = f"Boot {rek}"
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2), (1, 3)), soorten={1: "Kajak"})
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2)
    toewijzen(page, f"{rek}/1/1", bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    boot_openen(page, bootnaam)

    # Het blok staat dicht tussen de taak en Boot wijzigen; de keuzelijst begint leeg en toont geen eigen plaats.
    verplaatsen = page.locator("details.dj-disclosure", has=page.locator("summary#verplaatsen-kop"))
    expect(verplaatsen).not_to_have_attribute("open", "")
    expect(page.locator("section.kaart")).to_have_count(4)
    expect(page.locator("section.kaart").nth(1).locator("summary")).to_have_text("Boot verplaatsen")
    expect(page.get_by_text("Vrijgeven doe je op de plaats.")).to_be_visible()
    for breedte in (360, 1100):
        page.set_viewport_size({"width": breedte, "height": 900})
        blok_openen(page, "Boot verplaatsen")
        keuze = page.get_by_label("Verplaats naar een vrije plaats voor kajak")
        expect(keuze).to_have_value("")
        opties = keuze.locator("option").all_inner_texts()
        assert opties[0] == "Kies een vrije plaats" and f"{rek}/1/2 (rek {rek})" in opties
        assert f"{rek}/1/1 (rek {rek})" not in opties
        expect(page.get_by_role("button", name="Verplaats", exact=True)).to_be_visible()
        past_in_de_kaart(page, "verplaatsen-kop")
        # designsystem gh#50: de knop Boot ... verwijderen in Boot wijzigen loopt op 360 px buiten de kaart; speelt nog, niet hier getoetst.
    page.set_viewport_size({"width": 1100, "height": 900})

    # Weigering: een andere beheerder (tweede tabblad, zelfde sessie) bezet de gekozen plaats eerst.
    keuze.select_option(label=f"{rek}/1/3 (rek {rek})")
    ander = page.context.new_page()
    boot_vastleggen(ander, f"Ander {rek}", "Kajak", eigenaar_index=3)
    toewijzen(ander, f"{rek}/1/3", f"Ander {rek}")
    expect(ander.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    ander.close()
    page.get_by_role("button", name="Verplaats", exact=True).click()
    expect(page.get_by_text(f"Plaats {rek}/1/3 is niet meer vrij. De boot blijft op {rek}/1/1.")).to_be_visible()
    expect(page.locator("details.dj-disclosure[open] > summary#verplaatsen-kop")).to_be_visible()  # open na een weigering
    expect(page.locator("dt", has_text="Plaats").locator("xpath=following-sibling::dd[1]")).to_have_text(f"{rek}/1/1")

    # Verplaatsen slaagt: de boot ligt op de nieuwe plaats, de oude is vrij, het log noemt het.
    page.get_by_label("Verplaats naar een vrije plaats voor kajak").select_option(label=f"{rek}/1/2 (rek {rek})")
    page.get_by_role("button", name="Verplaats", exact=True).click()
    expect(page.get_by_text("De boot is verplaatst.")).to_be_visible()
    expect(page.get_by_role("heading", name=f"Op plaats {rek}/1/2")).to_be_visible()
    expect(page.locator("details.dj-disclosure", has=page.locator("summary#verplaatsen-kop"))).not_to_have_attribute("open", "")
    blok_openen(page, "Log")
    expect(page.locator("section.log")).to_contain_text("boot.verplaatst")
    page.get_by_role("link", name=f"Naar plaats {rek}/1/2").click()
    expect(page.get_by_role("link", name=bootnaam, exact=True)).to_be_visible()  # de boot ligt op de nieuwe plaats
    page.goto("/indeling")
    page.get_by_role("link", name=f"{rek}/1/1", exact=True).click()
    expect(page.get_by_role("heading", name="Deze plaats is vrij")).to_be_visible()
