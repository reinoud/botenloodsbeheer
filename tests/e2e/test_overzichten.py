"""Overzichten, Excel-export en huisstijl (BLB-015 tot en met 019, BLB-027). Het testlogo komt
uit compose.dev.yml (ADR-008).

Elke test gebruikt een eigen uitnodiging en eigen plaatsen met de stempel van de run. De leden en
de oud-leden met een plaats komen uit flask seed (draai.sh)."""

import io
import re
import zipfile

from conftest import STEMPEL, reknaam, uitloggen, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import rek_met_plaats


def test_vrije_plaatsen_indeling_op_telefoon_en_export(page):
    wachtwoord_instellen(page, "vrij")
    ski = rek_met_plaats(page, reknaam("v"), ["Surfski"])
    club = rek_met_plaats(page, reknaam("w"), ["Surfski"], club=True)

    kajak = rek_met_plaats(page, reknaam("y"), ["Kajak"])
    meldingen = []
    page.on("console", lambda m: meldingen.append(m.text) if m.type == "error" else None)
    page.goto("/vrij")
    page.get_by_label("Geschikt voor").select_option(label="Surfski")
    page.wait_for_url(re.compile(r"/vrij\?bootsoort=\d+$"))
    expect(page.get_by_label("Geschikt voor")).to_be_focused()
    expect(page.get_by_role("link", name=ski, exact=True)).to_be_visible()
    expect(page.get_by_role("link", name=club, exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name=kajak, exact=True)).to_have_count(0)
    for rij in page.locator("main > .ds-table-wrap > table tbody tr").all():
        expect(rij.locator("td").nth(2)).to_contain_text("Surfski")
    page.get_by_label("Geschikt voor").select_option(label="Alle bootsoorten")
    page.wait_for_url(re.compile(r"/vrij\?bootsoort=$"))
    expect(page.get_by_role("link", name=kajak, exact=True)).to_be_visible()
    expect(page.get_by_role("link", name=ski, exact=True)).to_be_visible()
    assert not meldingen, meldingen

    page.set_viewport_size({"width": 360, "height": 740})
    page.goto("/indeling")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    expect(page.locator("tr", has=page.get_by_role("link", name=club, exact=True))).to_contain_text(
        "clubplaats")
    page.get_by_role("link", name=ski, exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_have_text(f"Plaats {ski}")

    page.goto("/indeling")
    with page.expect_download() as download:
        page.get_by_role("link", name="Indeling exporteren naar Excel").click()
    with zipfile.ZipFile(io.BytesIO(open(download.value.path(), "rb").read())) as xlsx:
        teksten = "".join(xlsx.read(n).decode() for n in xlsx.namelist() if n.startswith("xl/"))
    assert ski in teksten and "Lidnummer" in teksten
    # Vrije plaats en clubplaats zonder boot (BLB-017 criterium 3).
    assert "(geschikt voor Surfski)" in teksten
    assert "@example.org" not in teksten and "Peddelpad" not in teksten and "06-0000" not in teksten


def test_lid_zoeken_en_plaatsen_van_opgezegde_leden(page):
    wachtwoord_instellen(page, "leden")
    page.goto("/leden")
    page.get_by_label("Zoek op naam of lidnummer").fill("1001")
    page.get_by_role("button", name="Zoeken").click()
    leden = page.locator("main > .ds-table-wrap > table tbody tr")
    expect(leden).to_have_count(1)
    leden.get_by_role("link").click()
    expect(page.get_by_role("heading", name="Boten in de loods")).to_be_visible()
    expect(page.locator("main")).to_contain_text("Lidnummer 1001")
    assert "@example.org" not in page.content()

    page.goto("/opgezegd")
    rijen = page.locator("main > .ds-table-wrap > table tbody tr")
    expect(rijen.first).to_be_visible()  # de seed heeft oud-leden met een plaats
    datums = [re.sub(r"(\d+)-(\d+)-(\d+)", r"\3\2\1", t)
              for t in rijen.locator("td[data-label='Opgezegd op']").all_inner_texts()]
    assert datums == sorted(datums)
    code = rijen.first.locator("td[data-label='Plaats']").inner_text()
    rijen.first.get_by_role("link", name=code, exact=True).click()
    expect(page.get_by_role("button", name=f"Plaats {code} vrijgeven")).to_be_visible()


def test_naam_instellen_en_terugzetten(page, browser, base_url):
    wachtwoord_instellen(page, "huisstijl")
    code = rek_met_plaats(page, reknaam("h"), ["Kajak"])
    page.get_by_role("link", name=code, exact=True).click()
    openbare_link = page.locator("#openbare-link").get_attribute("href")

    page.goto("/instellingen")
    oud = page.locator("#naam").input_value()
    try:
        naam = f"KV Proef {STEMPEL}"
        page.get_by_label("Naam van de vereniging").fill(naam)
        page.get_by_role("button", name="Opslaan", exact=True).click()
        expect(page.get_by_text("De instellingen zijn opgeslagen.")).to_be_visible()
        expect(page.get_by_role("alert")).to_have_count(0)  # geen contrastwaarschuwing meer: de kleuren vervielen (#150)
        expect(page.locator("section.log")).to_have_count(0)  # BLB-043: alleen technisch log
        page.goto("/log/techniek")
        expect(page.locator("section.log")).to_contain_text("instelling.gewijzigd")
        page.goto("/instellingen")

        # De kleuren staan vast in de huisstijl (#150): geen kleurkiezer en geen stylesheet van de beheerder.
        expect(page.locator("input[type=color]")).to_have_count(0)
        expect(page.locator("link[href*='huisstijl.css']")).to_have_count(0)
        # Het logo komt uit de installatie: geen upload in de applicatie (BLB-027 criterium 4).
        expect(page.locator("input[type=file]")).to_have_count(0)
        expect(page.get_by_text("Het logo staat in de installatie")).to_be_visible()

        bezoeker = browser.new_page(base_url=base_url)
        bezoeker.goto(openbare_link)
        expect(bezoeker.locator(".kop-naam")).to_have_text(naam)
        logo = bezoeker.locator(".kop-naam img.logo")
        expect(logo).to_be_visible()
        expect(logo).to_have_attribute("src", re.compile(r"^/logo/[0-9a-f]{16}$"))
        # Rubik en PT Sans komen als woff2 uit /static en laden onder de CSP (default-src 'self').
        geladen = bezoeker.evaluate("document.fonts.ready.then(() => [...document.fonts]"
                                    ".filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight))")
        assert {"Rubik 700", "PT Sans 400"} <= {f.replace('"', '') for f in geladen}  # kop en lopende tekst
        bezoeker.close()
    finally:
        # Ook na een fout terugzetten, zodat andere tests en de handmatige route de oude naam zien.
        page.goto("/instellingen")
        page.get_by_label("Naam van de vereniging").fill(oud)
        page.get_by_role("button", name="Opslaan", exact=True).click()
        expect(page.locator(".kop-naam")).to_have_text(oud)
    uitloggen(page)
