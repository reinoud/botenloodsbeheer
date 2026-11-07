"""Bootsoorten beheren (BLB-028), de route uit issue #56: toevoegen, gebruiken bij een plaats en
een boot, hernoemen, verwijderen geweigerd, en na opruimen verwijderen. De soort heeft de stempel
van de run en wordt ook bij een fout opgeruimd, zodat de lijst van de gedeelde stack gelijk blijft."""

from conftest import STEMPEL, reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, rek_met_plaats


def rij(page, naam):
    return page.locator("section.kaart", has=page.get_by_role("heading", name="Bootsoorten")) \
        .locator("tbody tr", has=page.get_by_role("cell", name=naam, exact=True))


def test_bootsoort_toevoegen_hernoemen_en_verwijderen(page):
    wachtwoord_instellen(page, "bootsoorten")
    nieuw, ander = f"Waterfiets {STEMPEL}", f"Pedalo {STEMPEL}"
    rek, bootnaam = reknaam("s"), f"Trapper {STEMPEL}"
    boot = None
    page.goto("/instellingen")
    page.get_by_label("Nieuwe bootsoort").fill(nieuw)
    page.get_by_role("button", name="Bootsoort toevoegen").click()
    expect(page.get_by_text("De bootsoort is toegevoegd.")).to_be_visible()
    try:
        # Criterium 1: te kiezen bij plaatsen en boten.
        code = rek_met_plaats(page, rek, [nieuw])
        boot_vastleggen(page, bootnaam, nieuw)
        boot = page.url

        # Criterium 3: hernoemen; boot en plaats tonen de nieuwe naam en blijven gelijk.
        page.goto("/instellingen")
        page.get_by_label(f"Nieuwe naam voor {nieuw}").fill(ander)
        rij(page, nieuw).get_by_role("button", name="Naam opslaan").click()
        expect(page.get_by_text("De naam van de bootsoort is opgeslagen.")).to_be_visible()
        page.goto(boot)
        expect(page.locator("main")).to_contain_text(ander)
        page.goto("/indeling")
        expect(page.locator("tr", has=page.get_by_role("link", name=code, exact=True))).to_contain_text(ander)
        page.goto("/log/techniek")
        expect(page.locator("section.log")).to_contain_text(nieuw)
        expect(page.locator("section.log")).to_contain_text(ander)

        # Criterium 2: in gebruik, dus geweigerd.
        page.goto("/instellingen")
        rij(page, ander).get_by_role("button", name=f"{ander} verwijderen").click()
        expect(page.get_by_role("alert")).to_contain_text("in gebruik bij 1 boot en 1 plaats")
        expect(rij(page, ander)).to_have_count(1)
    finally:
        if boot:
            page.goto(boot)
            page.get_by_role("button", name=f"Boot {bootnaam} verwijderen").click()
        page.goto("/indeling")
        sectie = page.locator("section.dj-panel", has=page.get_by_role("heading", name=rek, exact=True))
        if sectie.count():
            sectie.get_by_text("Rek wijzigen of verwijderen").click()
            sectie.get_by_role("button", name=f"Rek {rek} verwijderen").click()
        page.goto("/instellingen")
        for naam in (nieuw, ander):
            if rij(page, naam).count():
                rij(page, naam).get_by_role("button", name=f"{naam} verwijderen").click()
    expect(page.get_by_text("De bootsoort is verwijderd.")).to_be_visible()
    expect(rij(page, ander)).to_have_count(0)
