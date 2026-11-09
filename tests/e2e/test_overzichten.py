"""Overzichten, Excel-export en huisstijl (BLB-015 tot en met 019, BLB-027). Het testlogo wordt
geüpload op Instellingen (issue #186, ADR-008).

Elke test gebruikt een eigen uitnodiging en eigen plaatsen met de stempel van de run. De leden en
de oud-leden met een plaats komen uit flask seed (draai.sh)."""

import io
import re
import zipfile
from pathlib import Path

from conftest import (
    LOGO,
    STEMPEL,
    afbeelding_geladen,
    blok_openen,
    logo_uploaden,
    reknaam,
    uitloggen,
    wachtwoord_instellen,
)
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
    expect(page).to_have_url(re.compile(r"/vrij$"))  # de keuzelijst verstuurt niet zelf (WCAG 3.2.2)
    page.get_by_role("button", name="Toon vrije plaatsen").click()
    page.wait_for_url(re.compile(r"/vrij\?bootsoort=\d+$"))
    expect(page.get_by_label("Geschikt voor")).to_be_focused()
    expect(page.get_by_role("link", name=ski, exact=True)).to_be_visible()
    expect(page.get_by_role("link", name=club, exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name=kajak, exact=True)).to_have_count(0)
    for rij in page.locator("main > .ds-table-wrap > table tbody tr").all():
        expect(rij.locator("td").nth(2)).to_contain_text("Surfski")
    page.get_by_label("Geschikt voor").select_option(label="Alle bootsoorten")
    page.get_by_role("button", name="Toon vrije plaatsen").click()
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


def test_lid_zoeken_en_plaatsen_van_opgezegde_leden(page):
    wachtwoord_instellen(page, "leden")
    page.goto("/leden")
    page.get_by_label("Zoek op naam of lidnummer").fill("1001")
    page.locator("main").get_by_role("button", name="Zoeken").click()
    leden = page.locator("main > ul.bl-lijst > li")
    expect(leden).to_have_count(1)
    leden.get_by_role("link").click()
    expect(page.get_by_role("heading", name="Boten in de loods")).to_be_visible()
    expect(page.locator("main")).to_contain_text("Lidnummer 1001")

    page.goto("/opgezegd")
    rijen = page.locator("main > ul.bl-lijst > li")
    expect(rijen.first).to_be_visible()  # de seed heeft oud-leden met een plaats
    datums = [re.sub(r"(\d+)-(\d+)-(\d+)", r"\3\2\1", t)
              for t in rijen.locator("[data-label='Opgezegd op']").all_inner_texts()]
    assert datums == sorted(datums)
    code = rijen.first.locator("[data-label='Plaats']").inner_text()
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
        # Het logo: uploaden, ongeldig bestand, vervangen, verwijderen (issue #186). Het begin is
        # schoon, ook als een eerdere test een logo achterliet.
        koplogo = "header .dj-logo img.bl-logo"
        blok_openen(page, "Logo")
        if page.get_by_role("button", name="Logo verwijderen").count():
            page.get_by_role("button", name="Logo verwijderen").click()
            expect(page.get_by_text("Het logo is verwijderd.")).to_be_visible()
            blok_openen(page, "Logo")
        expect(page.get_by_text("Er is geen logo.")).to_be_visible()
        expect(page.get_by_role("button", name="Logo verwijderen")).to_have_count(0)
        expect(page.locator(koplogo)).to_have_count(0)  # zonder logo alleen de naam
        expect(page.locator("header .dj-logo")).to_have_text(naam)

        logo_uploaden(page)  # mutant: de route /logo/ geeft 404 -> afbeelding_geladen faalt
        expect(page.locator(koplogo)).to_have_attribute("src", re.compile(r"^/logo/[\w-]{16}$"))
        afbeelding_geladen(page.locator(koplogo))
        eerste = page.locator(koplogo).get_attribute("src")
        blok_openen(page, "Logo")
        expect(page.get_by_role("button", name="Logo verwijderen")).to_be_visible()
        expect(page.get_by_alt_text("Huidig logo")).to_have_attribute("src", eerste)

        # Een ongeldig bestand: één melding, het blok staat open en het vorige logo blijft.
        page.get_by_label("Nieuw logo").set_input_files(
            {"name": "geheim.png", "mimeType": "image/png", "buffer": b"geen afbeelding"})
        page.get_by_role("button", name="Logo opslaan").click()
        expect(page.get_by_role("alert")).to_have_count(1)
        expect(page.get_by_role("alert")).to_have_text(
            "Dit bestand is geen geldige afbeelding in JPEG, PNG of WebP. De vorige blijft staan.")
        assert "geheim" not in page.content()  # de bestandsnaam komt nergens terug
        expect(page.locator("details.dj-disclosure[open] > summary", has_text="Logo")).to_be_visible()
        expect(page.locator(koplogo)).to_have_attribute("src", eerste)

        # Vervangen door een bestand van 1,5 MB: boven de 1 MB van de algemene router, dus alleen
        # de router van /instellingen/logo (10 MB) laat het door. Een nieuw logo geeft een nieuwe URL.
        # mutant: het label van router -logo weghalen -> Traefik geeft 413.
        groot = Path(LOGO).read_bytes() + b"\0" * 1_500_000
        page.get_by_label("Nieuw logo").set_input_files(
            {"name": "logo.png", "mimeType": "image/png", "buffer": groot})
        page.get_by_role("button", name="Logo opslaan").click()
        expect(page.get_by_text("Het logo is opgeslagen.")).to_be_visible()
        tweede = page.locator(koplogo).get_attribute("src")
        assert tweede != eerste
        afbeelding_geladen(page.locator(koplogo))

        # Elke bezoeker ziet het nieuwe logo direct, zonder inloggen.
        bezoeker = browser.new_page(base_url=base_url)
        bezoeker.goto(openbare_link)
        expect(bezoeker.locator(".dj-logo")).to_have_text(naam)
        logo = bezoeker.locator(".dj-logo img.bl-logo")
        expect(logo).to_be_visible()
        expect(logo).to_have_attribute("src", tweede)
        afbeelding_geladen(logo)
        # Rubik en PT Sans komen als woff2 uit /static en laden onder de CSP (default-src 'self').
        geladen = bezoeker.evaluate("document.fonts.ready.then(() => [...document.fonts]"
                                    ".filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight))")
        assert {"Rubik 700", "PT Sans 400"} <= {f.replace('"', '') for f in geladen}  # kop en lopende tekst

        # Verwijderen: de kopbalk en de openbare pagina tonen alleen de naam.
        page.goto("/instellingen")
        blok_openen(page, "Logo")
        page.get_by_role("button", name="Logo verwijderen").click()
        expect(page.get_by_text("Het logo is verwijderd.")).to_be_visible()
        expect(page.locator(koplogo)).to_have_count(0)
        bezoeker.reload()
        expect(bezoeker.locator(".dj-logo")).to_have_text(naam)
        expect(bezoeker.locator(".dj-logo img")).to_have_count(0)
        bezoeker.close()
        page.goto("/log/techniek")
        for actie in ("instelling.logo_toegevoegd", "instelling.logo_vervangen", "instelling.logo_verwijderd"):
            expect(page.locator("section.log")).to_contain_text(actie)
    finally:
        # Ook na een fout terugzetten, zodat andere tests en de handmatige route de oude naam zien.
        page.goto("/instellingen")
        page.get_by_label("Naam van de vereniging").fill(oud)
        page.get_by_role("button", name="Opslaan", exact=True).click()
        expect(page.locator(".dj-logo")).to_have_text(oud)
    uitloggen(page)
