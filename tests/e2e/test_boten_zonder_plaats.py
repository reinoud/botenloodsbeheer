"""Boten zonder plaats (#399), de route voor een mens: kies in het menu onder Dagelijks de lijst, zet een boot met
één klik op de wachtlijst (vandaag) en zie dat een clubboot geen knop heeft. Daarna leest een kijker dezelfde
lijst zonder knop en zonder status. De selectie en de knopregels staan in de unittests."""

from datetime import date

from conftest import STEMPEL, gebruikersnaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen


def regel_van(page, boot):
    return page.locator("main > ul.bl-lijst > li").filter(has=page.get_by_role("link", name=boot, exact=True))


def test_beheerder_zet_een_boot_op_de_wachtlijst_en_een_kijker_leest_mee(page, browser, base_url):
    wachtwoord_instellen(page, "zonderplaats")
    gewoon, club = f"Plaatsloos {STEMPEL}", f"Clubje {STEMPEL}"
    boot_vastleggen(page, gewoon, "Kajak", eigenaar_index=2)
    boot_vastleggen(page, club, "Kajak")

    page.goto("/rekoverzicht")
    dagelijks = page.locator("nav[aria-label='Hoofdmenu'] ul[aria-labelledby='menu-0'] a")
    namen = dagelijks.all_inner_texts()  # achter Boten zonder eigenaar kan een aantal staan
    eigenaar = next(i for i, n in enumerate(namen) if n.startswith("Boten zonder eigenaar"))
    assert namen[eigenaar + 1] == "Boten zonder plaats"
    page.get_by_role("link", name="Boten zonder plaats", exact=True).evaluate("e => e.click()")
    expect(page.get_by_role("heading", level=1)).to_have_text("Boten zonder plaats")
    expect(page.locator("a[aria-current='page']", has_text="Boten zonder plaats")).to_have_count(1)
    expect(regel_van(page, club)).to_contain_text("kan niet op de wachtlijst")
    expect(regel_van(page, club).get_by_role("button")).to_have_count(0)

    regel_van(page, gewoon).get_by_role("button", name=f"Zet {gewoon} op de wachtlijst").click()
    expect(page.get_by_text("De boot staat op de wachtlijst.")).to_be_visible()
    expect(page.get_by_role("heading", level=1)).to_have_text("Boten zonder plaats")
    expect(regel_van(page, gewoon)).to_contain_text(f"op de wachtlijst sinds {date.today():%d-%m-%Y}")
    expect(regel_van(page, gewoon).get_by_role("button")).to_have_count(0)

    # Een kijker leest dezelfde lijst, zonder knop, status en leden.
    nieuw = gebruikersnaam("kijkerplaats")
    page.goto("/gebruikers")
    page.get_by_label("Gebruikersnaam").fill(nieuw)
    page.get_by_role("radio", name="Kijker: ziet de loods en wijzigt niets").check()
    page.get_by_role("button", name="Uitnodigen").click()
    uitnodiging = page.locator("#uitnodigingslink").inner_text()
    kijker = browser.new_context(base_url=base_url).new_page()
    wachtwoord_instellen(kijker, None, url=uitnodiging)
    kijker.goto("/boten/zonder-plaats")
    expect(regel_van(kijker, gewoon)).to_be_visible()
    expect(kijker.locator("main button")).to_have_count(0)
    expect(kijker.locator("main a[href^='/leden']")).to_have_count(0)
    expect(kijker.get_by_text("wachtlijst", exact=False)).to_have_count(0)
