"""Filters zonder knop (#380, #395) op /vrij, /wachtlijst, /boten, /leden, /opgezegd en /opzeggend: een andere keuze filtert direct, zoeken
begint bij 3 tekens, alleen de lijst ververst en de focus blijft staan. Zonder script werkt de knop.
Eén inlogverzoek; de boten heten Zxq en Yxq met de stempel, zodat alleen de eigen rijen tellen."""

import re

from conftest import STEMPEL, reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, kiesbare_leden, rek_met_plaats

PAUZE_MS = 800  # ruim boven de 300 ms wachttijd na het typen


def op_de_wachtlijst(page, naam, soort):
    boot_vastleggen(page, naam, soort, eigenaar_index=2)
    page.get_by_role("button", name="Op de wachtlijst zetten").click()
    expect(page.get_by_text("De boot staat op de wachtlijst.")).to_be_visible()


def test_filters_zonder_knop_op_alle_lijsten(page, browser, base_url):
    wachtwoord_instellen(page, "lijstfilter")
    ski = rek_met_plaats(page, reknaam("lfs"), ["Surfski"])
    kajak = rek_met_plaats(page, reknaam("lfk"), ["Kajak"])
    zxq, yxq = f"Zxq {STEMPEL}", f"Yxq {STEMPEL}"
    op_de_wachtlijst(page, zxq, "Kajak")
    op_de_wachtlijst(page, yxq, "Surfski")
    meldingen, verzoeken = [], []
    page.on("console", lambda m: meldingen.append(m.text) if m.type == "error" else None)  # ook een CSP-fout
    page.on("request", lambda r: verzoeken.append(r.url) if r.resource_type in ("fetch", "xhr") else None)

    # Een keuze zonder klik: de knop is weg, de lijst verandert, de focus blijft, de URL volgt het formulier.
    for pad, knop, label, eigen, vreemd in (
            ("/vrij", "Toon vrije plaatsen", "Geschikt voor", ski, kajak),
            ("/wachtlijst", "Toon wachtlijst", "Alleen soort", yxq, zxq),
            ("/boten", "Toon boten", "Alleen soort", yxq, zxq)):
        page.goto(pad)
        expect(page.locator("main").get_by_role("button", name=knop)).to_be_hidden()
        page.get_by_label(label).focus()  # select_option zet de focus niet zelf
        page.get_by_label(label).select_option(label="Surfski")
        expect(page).to_have_url(re.compile(rf"{pad}\?(zoek=&)?bootsoort=\d+$"))
        expect(page.get_by_role("link", name=eigen, exact=True)).to_be_visible()
        expect(page.get_by_role("link", name=vreemd, exact=True)).to_have_count(0)
        expect(page.get_by_label(label)).to_be_focused()
        expect(page.get_by_role("status").filter(has_text=re.compile(r"^\d+ "))).to_have_count(1)  # het aantal treffers
        page.get_by_label(label).select_option(label="Alle bootsoorten")
        expect(page.get_by_role("link", name=vreemd, exact=True)).to_be_visible()
        expect(page).to_have_url(re.compile(rf"{pad}\?(zoek=&)?bootsoort=$"))

    # Zoeken: 2 tekens geen zoekactie, 3 tekens wel, de focus blijft in het zoekveld, wissen toont alles.
    for pad, label in (("/wachtlijst", "Zoek op boot of lid"), ("/boten", "Zoek op boot of lid")):
        page.goto(pad)
        veld = page.get_by_label(label)
        expect(page.get_by_text("Het zoeken start vanaf 3 tekens.")).to_be_visible()
        expect(veld).to_have_attribute("aria-describedby", re.compile(r"zoek-hint$"))  # het script koppelt de hint
        verzoeken.clear()
        veld.press_sequentially("Zx", delay=50)
        page.wait_for_timeout(PAUZE_MS)
        assert not verzoeken, verzoeken
        expect(page.get_by_role("link", name=yxq, exact=True)).to_be_visible()
        expect(page).not_to_have_url(re.compile("Zx"))
        veld.press_sequentially("q", delay=50)
        expect(page.get_by_role("link", name=yxq, exact=True)).to_have_count(0)
        expect(page.get_by_role("link", name=zxq, exact=True)).to_be_visible()
        expect(page).to_have_url(re.compile(r"zoek=Zxq"))
        expect(veld).to_be_focused()
        veld.press("Backspace")  # terug onder de 3 tekens: de term geldt niet meer
        expect(page.get_by_role("link", name=yxq, exact=True)).to_be_visible()
        expect(veld).to_be_focused()

    # Leden (#395): dezelfde afspraken, met een lidnummer uit de stack; het importblok blijft staan.
    (a, nr_a), (b, nr_b) = kiesbare_leden(page, 2)
    veld = page.get_by_label("Zoek op naam of lidnummer")
    expect(page.locator("main").get_by_role("button", name="Toon leden")).to_be_hidden()
    expect(page.get_by_text("Het zoeken start vanaf 3 tekens.")).to_be_visible()
    verzoeken.clear()
    veld.press_sequentially(nr_a[:2], delay=50)
    page.wait_for_timeout(PAUZE_MS)
    assert not verzoeken, verzoeken
    veld.fill(nr_a)
    expect(page.get_by_role("link", name=a, exact=True)).to_be_visible()
    # #400: het aantal boten staat na de live zoekactie achter de naam, buiten de link.
    rij = page.locator("li.bl-item").filter(has=page.get_by_role("link", name=a, exact=True)).first
    expect(rij.get_by_text(re.compile(r"^\((1 boot|(0|[2-9]|\d{2,}) boten)\)$"))).to_be_visible()
    if nr_a not in nr_b:
        expect(page.get_by_role("link", name=b, exact=True)).to_have_count(0)
    expect(page).to_have_url(re.compile(rf"/leden\?zoek={nr_a}$"))
    expect(page.get_by_role("status").filter(has_text=re.compile(r"^\d+ "))).to_have_count(1)
    expect(veld).to_be_focused()
    assert not meldingen, meldingen

    # Opgezegd en Gaan opzeggen (#403): zoeken zonder knop; een term zonder treffer geeft de melding.
    for pad, knop, label, leeg in (("/opgezegd", "Toon plaatsen", "Zoek op boot of oud-lid", "Geen plaatsen gevonden."),
                                   ("/opzeggend", "Toon boten", "Zoek op boot of lid", "Geen boten gevonden.")):
        page.goto(pad)
        veld = page.get_by_label(label)
        expect(page.locator("main").get_by_role("button", name=knop)).to_be_hidden()
        expect(page.get_by_text("Het zoeken start vanaf 3 tekens.")).to_be_visible()
        expect(veld).to_have_attribute("aria-describedby", re.compile(r"zoek-hint$"))
        verzoeken.clear()
        veld.press_sequentially("Qz", delay=50)
        page.wait_for_timeout(PAUZE_MS)
        assert not verzoeken, verzoeken
        veld.press_sequentially("xq", delay=50)
        expect(page.locator("main").get_by_text(leeg)).to_be_visible()
        expect(page.get_by_role("status").filter(has_text=leeg)).to_have_count(1)
        expect(page).to_have_url(re.compile(rf"{pad}\?zoek=Qzxq$"))
        expect(veld).to_be_focused()
    assert not meldingen, meldingen

    # Zonder JavaScript staat de knop er en filtert hij met een gewone GET.
    kaal = browser.new_context(base_url=base_url, java_script_enabled=False,
                               storage_state=page.context.storage_state()).new_page()
    kaal.goto("/wachtlijst")
    expect(kaal.get_by_label("Zoek op boot of lid")).not_to_have_attribute("aria-describedby", re.compile("."))
    expect(kaal.get_by_text("Het zoeken start vanaf 3 tekens.")).to_be_hidden()
    for pad, knop, label in (("/vrij", "Toon vrije plaatsen", "Geschikt voor"),
                             ("/wachtlijst", "Toon wachtlijst", "Alleen soort"),
                             ("/boten", "Toon boten", "Alleen soort")):
        kaal.goto(pad)
        kaal.get_by_label(label).select_option(label="Surfski")
        kaal.locator("main").get_by_role("button", name=knop).click()
        kaal.wait_for_url(re.compile(rf"{pad}\?(zoek=&)?bootsoort=\d+$"))
        expect(kaal.get_by_label(label).locator("option:checked")).to_have_text("Surfski")
        vreemd = kajak if pad == "/vrij" else zxq
        expect(kaal.get_by_role("link", name=vreemd, exact=True)).to_have_count(0)
    kaal.goto("/leden")
    kaal.get_by_label("Zoek op naam of lidnummer").fill(nr_a)
    kaal.locator("main").get_by_role("button", name="Toon leden").click()
    expect(kaal.get_by_role("link", name=a, exact=True)).to_be_visible()
    for pad, knop, label in (("/opgezegd", "Toon plaatsen", "Zoek op boot of oud-lid"),
                             ("/opzeggend", "Toon boten", "Zoek op boot of lid")):
        kaal.goto(pad)
        kaal.get_by_label(label).fill("Qzxq")
        kaal.locator("main").get_by_role("button", name=knop).click()
        kaal.wait_for_url(re.compile(rf"{pad}\?zoek=Qzxq$"))
        expect(kaal.locator("main").get_by_text("gevonden.")).to_be_visible()
    kaal.close()
