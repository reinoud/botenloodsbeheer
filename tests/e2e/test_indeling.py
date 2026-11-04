"""Indeling met rek, verdieping en vak (BLB-001, BLB-044, issues #80 en #83), de route voor een
mens: rek met gaten en een bootsoort per verdieping aanmaken, boot toewijzen aan <rek>/2/3 zonder
de plaats eerst in te stellen, uitzetten geweigerd, een vak later aanzetten, kaartje printen en de
openbare pagina openen via de QR-link. Eigen rek met een naam die per run uniek is."""

import re

from conftest import reknaam, uitloggen, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, rek_aanmaken, sectie_van, toewijzen

VAKKEN = ((1, 1), (1, 3), (1, 4), (1, 12), (2, 1), (2, 2), (2, 3), (2, 4))


def test_rek_met_gaten_boot_uitzetten_geweigerd_kaartje_en_openbare_pagina(page, browser, base_url):
    wachtwoord_instellen(page, "indelingraster")
    rek, omschrijving = reknaam("x"), "Testrek bij de deur"
    code = f"{rek}/2/3"
    bootnaam = f"Rasterboot {rek}"
    rek_aanmaken(page, rek, VAKKEN, omschrijving, soorten={1: "Surfski", 2: "Kajak"})

    # Alleen de vakken die aan stonden zijn plaatsen, ook met een gat (vak 2) en vak 12.
    sectie = sectie_van(page, rek)
    expect(sectie).to_contain_text(omschrijving)
    expect(sectie.locator("tbody a")).to_have_text([f"{rek}/{v}/{k}" for v, k in VAKKEN])
    expect(sectie.get_by_role("link", name=f"{rek}/1/2", exact=True)).to_have_count(0)

    # Elke plaats heeft de bootsoort van haar verdieping en er is geen knop om de plaats te
    # verwijderen. De boot hoeft dus niet eerst te worden ingesteld.
    page.get_by_role("link", name=f"{rek}/1/1", exact=True).click()
    expect(page.get_by_label("Surfski", exact=True)).to_be_checked()
    expect(page.get_by_label("Kajak", exact=True)).not_to_be_checked()
    expect(page.get_by_role("button", name=re.compile("verwijderen"))).to_have_count(0)
    page.go_back()
    page.get_by_role("link", name=code, exact=True).click()
    expect(page.get_by_label("Kajak", exact=True)).to_be_checked()
    boot_vastleggen(page, bootnaam, "Kajak", eigenaar_index=2)
    toewijzen(page, code, bootnaam)
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    expect(page.locator("main")).to_contain_text(omschrijving)
    prive = {veld: page.locator(f"[data-veld={veld}]").inner_text()
             for veld in ("naam", "lidnummer", "adres", "telefoon", "email")}
    assert all(prive.values())
    openbare_link = page.locator("#openbare-link").get_attribute("href")

    # Een vak met een boot kan niet uit; verandert er niets. Een vak zonder boot wel.
    page.goto("/indeling")
    sectie = sectie_van(page, rek)
    sectie.get_by_text("Rek wijzigen of verwijderen").click()
    sectie.get_by_label("Verdieping 2, vak 3", exact=True).uncheck()
    sectie.get_by_role("button", name="Indeling opslaan").click()
    expect(page.get_by_role("alert")).to_contain_text(f"Op plaats {code} ligt een boot")
    expect(sectie_van(page, rek).get_by_role("link", name=code, exact=True)).to_have_count(1)
    sectie = sectie_van(page, rek)
    sectie.get_by_text("Rek wijzigen of verwijderen").click()
    sectie.get_by_label("Verdieping 2, vak 4", exact=True).uncheck()
    sectie.get_by_role("button", name="Indeling opslaan").click()
    expect(page.get_by_text("De indeling is opgeslagen.")).to_be_visible()
    expect(sectie_van(page, rek).get_by_role("link", name=f"{rek}/2/4", exact=True)).to_have_count(0)
    expect(sectie_van(page, rek).get_by_role("link", name=code, exact=True)).to_have_count(1)

    # Een vak dat later aan gaat, krijgt de bootsoort van zijn verdieping.
    sectie = sectie_van(page, rek)
    sectie.get_by_text("Rek wijzigen of verwijderen").click()
    sectie.get_by_label("Verdieping 2, vak 5", exact=True).check()
    sectie.get_by_role("button", name="Indeling opslaan").click()
    expect(page.get_by_text("De indeling is opgeslagen.")).to_be_visible()
    sectie_van(page, rek).get_by_role("link", name=f"{rek}/2/5", exact=True).click()
    expect(page.get_by_label("Kajak", exact=True)).to_be_checked()

    # Het kaartje van de plaats: aanduiding, omschrijving en eigenaar, geen andere gegevens.
    page.goto("/kaartjes")
    page.get_by_label(code, exact=True).check()
    page.get_by_role("button", name="Kaartjes maken").click()
    page.wait_for_load_state()
    kaartje = page.locator("section.kaartje")
    expect(kaartje).to_have_count(1)
    expect(kaartje.locator(".kaartje-code")).to_have_text(code)
    expect(kaartje.locator(".kaartje-omschrijving")).to_have_text(omschrijving)
    expect(kaartje.locator(".kaartje-eigenaar")).to_have_text(prive["naam"])
    html = page.content()
    for veld in ("lidnummer", "adres", "telefoon", "email"):
        assert prive[veld] not in html, veld
    assert bootnaam not in html

    # De link uit de QR-code, als bezoeker zonder inloggen: aanduiding en omschrijving, en in de
    # hele respons geen adres, telefoon, e-mail of lidnummer.
    uitloggen(page)
    bezoeker = browser.new_page(base_url=base_url)
    antwoord = bezoeker.goto(openbare_link)
    assert antwoord.status == 200
    expect(bezoeker.get_by_role("heading", level=1)).to_have_text(f"Plaats {code}")
    expect(bezoeker.locator("main")).to_contain_text(omschrijving)
    expect(bezoeker.get_by_text(bootnaam)).to_be_visible()
    expect(bezoeker.get_by_text(prive["naam"], exact=True)).to_be_visible()
    respons = antwoord.text()
    for veld in ("lidnummer", "adres", "telefoon", "email"):
        assert prive[veld] not in respons, veld
    bezoeker.close()
    page.goto("/indeling")
    expect(page).to_have_url(re.compile(r"/inloggen$"))
