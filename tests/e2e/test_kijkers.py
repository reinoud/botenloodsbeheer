"""Kijkers (BLB-050, BLB-051, ADR-015, issue #322): een beheerder nodigt een kijker uit, de kijker ziet de loods
zonder knoppen en de server weigert zijn mutaties, ook met een geldig CSRF-token via Traefik. De rol geldt
zonder opnieuw inloggen. De uitnodigingen "kijkers" en "kijkerzelf" uit draai.sh zijn de beheerders van de twee tests.

De E2E-asserties zijn niet gemuteerd; de unittests in tests/unit/test_kijkers.py en test_gebruikers_rollen.py
dragen de mutanten."""

import re

from conftest import gebruikersnaam, menu_kiezen, menu_openen, uitloggen, wachtwoord_instellen
from playwright.sync_api import expect

# De foutpagina van de applicatie (#341); de 403 van Traefik is een kale "Forbidden".
APPLICATIE_403 = 'data-fout="403"'


def csrf(page):
    return page.locator('meta[name="csrf-token"]').get_attribute("content")


def get_geweigerd(page, pad):
    r = page.goto(pad)
    assert r.status == 403 and APPLICATIE_403 in r.text(), (pad, r.status)


def post_geweigerd(page, pad, **velden):
    """Een POST met een geldig CSRF-token geeft de 403 van de applicatie, niet die van de CSRF-controle (400)."""
    page.goto("/rekoverzicht")  # een pagina met het token
    r = page.request.post(pad, form={"csrf_token": csrf(page), **velden}, max_redirects=0)
    assert r.status == 403 and APPLICATIE_403 in r.text(), (pad, r.status)


def test_kijker_ziet_de_loods_zonder_knoppen_en_de_server_weigert_zijn_mutaties(page, browser, base_url):
    wachtwoord_instellen(page, "kijkers")
    nieuw = gebruikersnaam("kijkernieuw")
    menu_kiezen(page, "Beheer", "Gebruikers")
    page.get_by_label("Gebruikersnaam").fill(nieuw)
    expect(page.locator("input[type=radio][name=rol]")).to_have_count(2)  # zonder voorkeur (BV-91)
    expect(page.locator("input[type=radio][name=rol]:checked")).to_have_count(0)
    page.get_by_role("radio", name="Kijker: ziet de loods en wijzigt niets").check()
    page.get_by_role("button", name="Uitnodigen").click()
    uitnodiging = page.locator("#uitnodigingslink").inner_text()

    kijker = browser.new_context(base_url=base_url).new_page()
    wachtwoord_instellen(kijker, None, url=uitnodiging)

    # BV-100: dezelfde koppen als de beheerder, met alleen zijn items; Leden en Beheer ontbreken. Eerst smal, dan breed.
    menu = kijker.get_by_role("navigation", name="Hoofdmenu")
    for breedte in (360, 1280):
        kijker.set_viewport_size({"width": breedte, "height": 740})
        kijker.goto("/rekoverzicht")
        expect(menu.locator("details.dj-menu__kop > summary")).to_have_text(["Loods", "Boten", "Account"])
        expect(menu.locator("summary[aria-current='true']")).to_have_text("Loods")
        expect(menu_openen(kijker, "Loods").get_by_role("link")).to_have_text(["Rekoverzicht", "Vrije plaatsen"])
        expect(menu_openen(kijker, "Boten").get_by_role("link")).to_have_text(["Boten", "Boten zonder plaats"])
        expect(menu_openen(kijker, "Account").get_by_role("link")).to_have_text(["Profiel"])
        expect(menu.get_by_role("button", name="Uitloggen")).to_be_visible()
        # De open kop sluit bij Escape (menu.js) en de focus staat dan op de kop.
        kijker.keyboard.press("Escape")
        expect(menu.locator("details.dj-menu__kop[open]")).to_have_count(0)

    # Boten: geen Nieuwe boot; een boot: geen knoppen en de eigenaar zonder link.
    kijker.goto("/boten")
    expect(kijker.get_by_text("Nieuwe boot")).to_have_count(0)
    kijker.locator("a.bl-item__titel").first.click()
    boot_url = kijker.url
    boot_id = re.search(r"/boten/(\d+)$", boot_url).group(1)
    expect(kijker.locator("main button")).to_have_count(0)
    expect(kijker.locator("main a[href^='/leden']")).to_have_count(0)
    for tekst in ("Boot verplaatsen", "Boot wijzigen", "Foto vervangen", "Vrijgeven doe je op de plaats"):
        expect(kijker.get_by_text(tekst)).to_have_count(0)
    kijker.get_by_label("Overal zoeken").get_by_role("searchbox").fill("ab")
    kijker.get_by_label("Overal zoeken").get_by_role("button").click()
    expect(kijker.locator("main a[href^='/leden']")).to_have_count(0)

    # De server weigert elke pagina en elke mutatie buiten de lijst, ook met een geldig token.
    for pad in ("/leden", "/wachtlijst", "/log", "/log/techniek", "/indeling", "/tokens", "/tokens/nieuw", "/status",
                "/instellingen", "/gebruikers", "/beheerders"):
        get_geweigerd(kijker, pad)
    for pad in ("/leden/ophalen", f"/boten/{boot_id}/verwijderen", f"/boten/{boot_id}/verplaatsen", "/boten",
                "/plaatsen/1/vrijgeven", "/gebruikers", "/tokens/nieuw"):
        post_geweigerd(kijker, pad, naam="x", gebruikersnaam="x", rol="beheerder")
    kijker.goto(boot_url)  # de boot is er nog
    expect(kijker.get_by_role("heading", level=1)).to_be_visible()

    # Eigen profiel en uitloggen mogen wel (besluit 8): geen 403 op de POST-route van het profiel.
    menu_kiezen(kijker, "Account", "Profiel")
    expect(kijker.get_by_role("heading", level=1)).to_have_text(f"Profiel van {nieuw}")
    r = kijker.request.post("/profiel/intrekken", form={"csrf_token": csrf(kijker), "methode": "wachtwoord"},
                            max_redirects=0)
    assert r.status == 302, r.status  # "enige inlogmethode": het domein weigert, de rolcontrole niet

    # De rol geldt zonder opnieuw inloggen, in beide richtingen.
    page.goto("/gebruikers")
    expect(page.locator("tr", has_text=nieuw).locator("td[data-label='Rol']")).to_have_text("Kijker")
    page.get_by_role("button", name=f"Maak beheerder: {nieuw}").click()
    expect(page.get_by_text(f"{nieuw} is nu beheerder.")).to_be_visible()
    assert kijker.goto("/gebruikers").status == 200
    page.get_by_role("button", name=f"Maak kijker: {nieuw}").click()
    expect(page.get_by_text(f"De persoonlijke tokens van {nieuw} zijn ingetrokken.")).to_be_visible()
    assert kijker.goto("/gebruikers").status == 403
    page.goto("/log/techniek")
    expect(page.locator("section.log")).to_contain_text("beheerder.rol_gewijzigd")

    kijker.goto("/rekoverzicht")
    uitloggen(kijker)
    kijker.context.close()


def test_beheerder_maakt_zichzelf_kijker_en_landt_op_rekoverzicht_met_een_melding(page):
    wachtwoord_instellen(page, "kijkerzelf")
    eigen = gebruikersnaam("kijkerzelf")
    page.goto("/gebruikers")
    page.get_by_role("button", name=f"Maak kijker: {eigen}").click()
    expect(page).to_have_url(re.compile(r"/rekoverzicht$"))
    expect(page.get_by_role("status")).to_contain_text("Je bent nu kijker")
    assert page.goto("/gebruikers").status == 403
