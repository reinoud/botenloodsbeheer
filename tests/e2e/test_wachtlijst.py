"""Wachtlijst per bootsoort (BLB-013, BLB-014, BLB-011 criterium 3, BLB-019 criterium 1).

Volgt de route uit issue #43. Elke test maakt een eigen rek, plaats en boot met de stempel van
de run; de leden en de wachtlijst van seed komen uit draai.sh."""

from conftest import STEMPEL, reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, rek_met_plaats, toewijzen


def test_wachtlijst_erop_vrijgeven_en_toewijzen(page):
    wachtwoord_instellen(page, "wachtlijst")
    rek = reknaam("l")
    wachter, bezetter = f"Wachter {STEMPEL}", f"Bezetter {STEMPEL}"
    code = rek_met_plaats(page, rek, ["Surfski"])
    boot_vastleggen(page, bezetter, "Surfski", eigenaar_index=3)
    toewijzen(page, code, bezetter)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()

    # Een boot zonder plaats op de lijst, met een datum in het verleden.
    boot_vastleggen(page, wachter, "Surfski", eigenaar_index=2)
    boot = page.url
    page.get_by_label("Aanmelddatum (leeg is vandaag; een eerdere datum mag)").fill("2019-05-01")
    page.get_by_role("button", name="Op de wachtlijst zetten").click()
    expect(page.get_by_text("De boot staat op de wachtlijst.")).to_be_visible()
    expect(page.get_by_text("staat sinds 01-05-2019 op de wachtlijst voor surfski")).to_be_visible()
    eigenaar = page.locator("dd").nth(1).inner_text()

    # De lijst van surfski's: langst wachtende bovenaan, met wachttijd.
    page.goto("/wachtlijst")
    surfski = page.locator("section.kaart", has=page.get_by_role("heading", name="Surfski", exact=True))
    rij = surfski.locator("tbody tr", has_text=wachter)
    expect(rij).to_contain_text("01-05-2019")
    expect(rij.locator("td[data-label=Wachttijd]")).to_contain_text("jaar")
    datums = [d.split("-")[::-1] for d in
              surfski.locator("td[data-label='Aangemeld op']").all_inner_texts()]
    assert datums == sorted(datums)  # langst wachtende bovenaan; eerdere runs staan er ook op
    expect(page.locator("section.log")).to_contain_text("wachtlijst.toegevoegd")

    # BLB-019: de lijst per lid zegt dat de boot op de wachtlijst staat.
    page.get_by_role("link", name=eigenaar).first.click()
    expect(page.locator("tr", has=page.get_by_role("link", name=wachter))).to_contain_text(
        "Sinds 01-05-2019")

    # BLB-011 criterium 3: vrijgeven wijst niet zelf toe.
    page.goto("/indeling")
    page.get_by_role("link", name=code, exact=True).click()
    page.get_by_role("button", name=f"Plaats {code} vrijgeven").click()
    expect(page.get_by_text("De plaats is vrijgegeven.")).to_be_visible()
    page.reload()
    expect(page.get_by_role("heading", name="Deze plaats is vrij")).to_be_visible()

    # BLB-014: de beheerder kiest de boot van de lijst; daarna is hij eraf.
    wachtend = page.locator("optgroup[label^='Op de wachtlijst'] option", has_text=wachter)
    expect(wachtend).to_have_count(1)
    toewijzen(page, code, wachter)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    page.goto(boot)
    log = page.locator("section.log")
    expect(log).to_contain_text("wachtlijst.verwijderd")
    expect(log).to_contain_text("plaats toegewezen")
    page.goto("/wachtlijst")
    expect(page.get_by_role("link", name=wachter)).to_have_count(0)
    page.goto("/log/techniek")
    expect(page.locator("section.log")).not_to_contain_text("wachtlijst.")


def test_wachtende_boot_krijgt_plaats_vanaf_de_bootpagina(page):
    """#132: kies een vrije plaats op de bootpagina; de boot gaat van de wachtlijst."""
    wachtwoord_instellen(page, "bootplaats")
    wachter = f"Bootplaats {STEMPEL}"
    code = rek_met_plaats(page, reknaam("c"), ["Surfski"])
    boot_vastleggen(page, wachter, "Surfski", eigenaar_index=2)
    page.get_by_role("button", name="Op de wachtlijst zetten").click()
    expect(page.get_by_text("De boot staat op de wachtlijst.")).to_be_visible()
    keuze = page.locator("#plaats option", has_text=code).get_attribute("value")
    page.get_by_label("Vrije plaats voor surfski").select_option(value=keuze)
    page.get_by_role("button", name="Wijs toe aan plek").click()
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    expect(page.get_by_role("link", name=code, exact=True)).to_be_visible()
    expect(page.locator("section.log")).to_contain_text("wachtlijst.verwijderd")
    page.goto("/wachtlijst")
    expect(page.get_by_role("link", name=wachter)).to_have_count(0)


def test_wachtlijst_weigert_toekomst_en_clubboot_en_eraf_halen(page):
    wachtwoord_instellen(page, "wachtlijstfout")
    club, boot = f"Clubwachter {STEMPEL}", f"Toekomst {STEMPEL}"
    boot_vastleggen(page, club, "Kajak")
    expect(page.get_by_text("Een clubboot kan niet op de wachtlijst.")).to_be_visible()
    expect(page.get_by_role("button", name="Op de wachtlijst zetten")).to_have_count(0)

    boot_vastleggen(page, boot, "Kajak", eigenaar_index=4)
    veld = page.get_by_label("Aanmelddatum (leeg is vandaag; een eerdere datum mag)")
    veld.evaluate("e => e.removeAttribute('max')")  # de browser zou het al tegenhouden
    veld.fill("2099-01-01")
    page.get_by_role("button", name="Op de wachtlijst zetten").click()
    expect(page.get_by_text("De aanmelddatum mag niet in de toekomst liggen.")).to_be_visible()

    page.get_by_role("button", name="Op de wachtlijst zetten").click()  # leeg: vandaag
    expect(page.get_by_text("De boot staat op de wachtlijst.")).to_be_visible()
    page.goto("/wachtlijst")
    rij = page.locator("section.kaart tr", has_text=boot)
    expect(rij).to_contain_text("0 dagen")
    rij.get_by_role("button", name=f"{boot} van de lijst halen").click()
    expect(page.get_by_text("De boot is van de wachtlijst gehaald.")).to_be_visible()
    expect(page.get_by_role("link", name=boot)).to_have_count(0)
    expect(page.locator("section.log")).to_contain_text("wachtlijst.verwijderd")
