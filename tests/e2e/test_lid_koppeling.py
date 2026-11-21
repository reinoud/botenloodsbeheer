"""Een gebruiker koppelen aan een lid, op Gebruikers en de pagina per account (#353, BV-96): koppelen, een
kijker krijgt geen oud-lid als treffer, een beheerder wel, "Maak kijker" bij een oud-lid weigert, de status
meldt de beheerder met een oud-lid en de gebruikers zonder lid, loskoppelen. Eén inlog (de uitnodiging
"lidkoppeling"); de twee extra accounts heten e2e-lkkijker en e2e-lkbeheerder met de stempel, zodat opruimen.sql
ze meeneemt. Het oud-lid is een lid uit de fixture met een opzegdatum van 30 dagen geleden (zoals
test_oud_lid_boot.py); de fixture gaat daarna terug.

De opschoning zelf (de kijker met een oud-lid verdwijnt) draait op OPSCHOON_TIJDSTIP en is niet vanuit de browser
te starten: de unittests in tests/unit/test_opschonen.py dekken haar.

Mutanten (unit: tests/unit/test_lid_koppeling_web.py; E2E: een kopie van het sjabloon of de route als :ro bind mount,
zie overlay §4 E2E). Per assert staat achter de regel welke mutant hem vangt."""

import re
from datetime import date, timedelta

from conftest import gebruikersnaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_import import FIXTURE, roep

ACTIEF, OUD = FIXTURE[2], FIXTURE[3]


def account_uitnodigen(page, soort, rol):
    page.goto("/gebruikers")
    page.get_by_label("Gebruikersnaam").fill(gebruikersnaam(soort))
    page.get_by_role("radio", name=re.compile(f"^{rol}:", re.IGNORECASE)).check()
    page.get_by_role("button", name="Uitnodigen", exact=True).click()
    expect(page.locator("#uitnodigingslink")).to_be_visible()


def rij(page, soort):
    return page.locator("main tbody tr").filter(has=page.locator("[data-veld=gebruikersnaam]", has_text=gebruikersnaam(soort)))


def lid_zoeken(page, term):
    main = page.locator("main")
    main.get_by_label(re.compile("^Zoek (een ander )?lid")).fill(term)
    main.get_by_role("button", name="Zoeken", exact=True).click()


def treffer(page, lid):
    return page.locator("main fieldset.dj-choices label", has_text=f"({lid['lidnummer']})")


def test_koppelen_oud_lid_status_en_loskoppelen(page):
    wachtwoord_instellen(page, "lidkoppeling")
    oud = {**OUD, "opzegdatum": (date.today() - timedelta(days=30)).isoformat()}
    assert roep("PUT", "/leden", {"leden": [oud if r is OUD else r for r in FIXTURE]})[0] == 200
    try:
        account_uitnodigen(page, "lkkijker", "kijker")
        account_uitnodigen(page, "lkbeheerder", "beheerder")
        page.goto("/gebruikers")
        kijker, beheerder = gebruikersnaam("lkkijker"), gebruikersnaam("lkbeheerder")

        # Gebruikers: zonder koppeling de regel "niet gekoppeld" en de link Lid koppelen. Mutant: link- of hinttekst anders.
        expect(rij(page, "lkkijker").locator("[data-veld=lid]")).to_have_text("Lid: niet gekoppeld")
        expect(rij(page, "lkkijker").get_by_role("link")).to_have_text(f"Lid koppelen: {kijker}")
        expect(page.get_by_text("Het lid koppel je daarna in de lijst met accounts.")).to_be_visible()
        expect(page.locator("#lid-hint")).to_contain_text("verwijdert de nachtelijke opschoning dat account")
        expect(page.locator("main form[action='/gebruikers'] input[type=search]")).to_have_count(0)

        # Koppelen aan een actief lid. Mutant: route zonder commit, of redirect zonder flash.
        rij(page, "lkkijker").get_by_role("link").click()
        expect(page.get_by_role("heading", level=1)).to_have_text(f"Lid koppelen: {kijker}")
        expect(page.locator("main [data-veld=stand]")).to_have_text("Rol: Kijker. Nu gekoppeld aan: niemand.")
        expect(page.get_by_role("button", name="Koppelen", exact=True)).to_have_count(0)  # eerst zoeken
        expect(page.get_by_role("button", name="Lid loskoppelen")).to_have_count(0)
        lid_zoeken(page, ACTIEF["lidnummer"])
        expect(treffer(page, ACTIEF)).to_have_count(1)
        expect(treffer(page, ACTIEF).locator(".ds-tag")).to_have_count(0)
        page.get_by_role("button", name="Koppelen", exact=True).click()
        expect(page.get_by_role("status").filter(has_text="is gekoppeld aan")).to_have_text(
            f"{kijker} is gekoppeld aan {ACTIEF['naam']} ({ACTIEF['lidnummer']}).")
        expect(rij(page, "lkkijker").locator("[data-veld=lid]")).to_have_text(f"Lid: {ACTIEF['naam']} ({ACTIEF['lidnummer']})")
        expect(rij(page, "lkkijker").get_by_role("link")).to_have_text(f"Lid wijzigen: {kijker}")

        # Een kijker krijgt een oud-lid niet als treffer. Mutant: oud=True in _lid_veld.
        rij(page, "lkkijker").get_by_role("link").click()
        expect(page.get_by_role("heading", level=1)).to_have_text(f"Lid wijzigen: {kijker}")
        lid_zoeken(page, OUD["lidnummer"])
        expect(page.locator("#lid-zoek-fout")).to_have_text("Geen lid gevonden. Zoek op een deel van de naam of op het lidnummer.")
        expect(page.locator("#lid-zoek")).to_have_attribute("aria-invalid", "true")
        expect(treffer(page, OUD)).to_have_count(0)

        # Koppelen zonder keuze: de fout bij het zoekveld en niets losgemaakt. Mutant: lid None valt door naar loskoppelen.
        lid_zoeken(page, ACTIEF["naam"].split()[0])
        assert page.locator("main fieldset.dj-choices input[type=radio]").count() >= 2
        page.get_by_role("button", name="Koppelen", exact=True).click()
        expect(page.locator("#lid-zoek-fout")).to_have_text("Kies een lid uit de treffers. Zoek eerst met de knop Zoeken.")
        page.goto("/gebruikers")
        expect(rij(page, "lkkijker").locator("[data-veld=lid]")).to_contain_text(ACTIEF["lidnummer"])

        # Een beheerder mag aan een oud-lid; de treffer en de regel dragen de tag. Mutant: oud=False, of de tag weg.
        rij(page, "lkbeheerder").get_by_role("link").click()
        lid_zoeken(page, OUD["lidnummer"])
        expect(treffer(page, OUD).locator(".ds-tag")).to_have_text("oud-lid")
        page.get_by_role("button", name="Koppelen", exact=True).click()
        expect(rij(page, "lkbeheerder").locator("[data-veld=lid] .ds-tag")).to_have_text("oud-lid")
        expect(page.locator("main .ds-tag")).to_have_count(1)

        # Maak kijker bij een oud-lid weigert en wijzigt niets. Mutant: de controle in rol_wijzigen weg, of een andere tekst.
        page.get_by_role("button", name=f"Maak kijker: {beheerder}").click()
        expect(page.get_by_role("alert")).to_have_text(
            f"{beheerder} is niet kijker gemaakt: het gekoppelde lid is oud-lid. Een kijker met een oud-lid verwijdert "
            "de nachtelijke opschoning. Maak eerst de koppeling los of laat het account beheerder.")
        expect(rij(page, "lkbeheerder").locator("td[data-label=Rol]")).to_have_text("Beheerder")

        # Status: de beheerder met een oud-lid en de accounts zonder lid, in HTML en JSON. Mutant: een rij zonder aantalcontrole
        # valt hier niet (het aantal is boven nul); dat dekt de unittest met nul.
        page.goto("/status")
        expect(page.locator("tr", has=page.locator("td", has_text="Beheerders met een oud-lid"))).to_contain_text(beheerder)
        expect(page.locator("tr", has=page.locator("td", has_text="Gebruikers zonder lid"))).to_contain_text(
            gebruikersnaam("lidkoppeling"))
        expect(page.locator("tr", has=page.locator("td", has_text="Gebruikers zonder lid"))).not_to_contain_text(kijker)
        s = page.request.get("/status.json").json()
        assert beheerder in s["beheerders_oud_lid"]["gebruikers"] and s["beheerders_oud_lid"]["status"] == "waarschuwing"
        assert gebruikersnaam("lidkoppeling") in s["niet_gekoppeld"]["gebruikers"] and kijker not in s["niet_gekoppeld"]["gebruikers"]
        for tekst in (page.content(), str(s)):
            assert OUD["naam"] not in tekst and OUD["lidnummer"] not in tekst  # geen lidgegevens op de status

        # Loskoppelen. Mutant: actie loskoppelen zonder effect.
        page.goto("/gebruikers")
        rij(page, "lkkijker").get_by_role("link").click()
        page.get_by_role("button", name=f"Lid loskoppelen: {kijker}").click()
        expect(page.get_by_role("status").filter(has_text="losgemaakt")).to_have_text(
            f"De koppeling van {kijker} met een lid is losgemaakt.")
        expect(rij(page, "lkkijker").locator("[data-veld=lid]")).to_have_text("Lid: niet gekoppeld")
        page.goto("/status")
        expect(page.locator("tr", has=page.locator("td", has_text="Gebruikers zonder lid"))).to_contain_text(kijker)
    finally:
        assert roep("PUT", "/leden", {"leden": FIXTURE})[0] == 200
