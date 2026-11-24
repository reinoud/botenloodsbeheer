"""Een boot van een oud-lid vastleggen en een plaats geven (#298), de route voor een mens: zoek het
oud-lid bij Nieuwe boot (de treffer draagt de tag oud-lid), leg de boot vast, geef hem een plaats,
zie hem op Opgezegd, en zie dat een tweede boot van het oud-lid niet op de wachtlijst kan.
Het oud-lid is een lid uit de fixture met een opzegdatum van 30 dagen geleden, via dezelfde volledige
PUT als test_import.py (die zet de fixture daarna terug)."""

from datetime import date, timedelta

from conftest import STEMPEL, reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_import import FIXTURE, roep
from test_loods import lid_zoeken_en_kiezen, rek_met_plaats


def oud_lid_binnen_de_termijn():
    gekozen = FIXTURE[0]
    maand_geleden = (date.today() - timedelta(days=30)).isoformat()
    lijst = [{**r, "opzegdatum": maand_geleden} if r is gekozen else r for r in FIXTURE]
    assert roep("PUT", "/leden", {"leden": lijst})[0] == 200
    return gekozen


def boot_vastleggen_voor_oud_lid(page, naam, lidnummer):
    page.goto("/boten")
    page.get_by_text("Nieuwe boot", exact=True).click()
    formulier = page.locator("details.bl-nieuw form")
    formulier.get_by_label("Naam van de boot").fill(naam)
    formulier.get_by_label("Bootsoort").select_option(label="Kajak")
    lid_zoeken_en_kiezen(formulier.get_by_label("Eigenaar", exact=True),
                         formulier.get_by_role("button", name="Zoeken", exact=True), lidnummer)
    treffer = formulier.locator("fieldset.dj-choices label", has_text=f"({lidnummer})")
    expect(treffer.locator(".ds-tag")).to_have_text("oud-lid")
    page.get_by_role("button", name="Boot vastleggen").click()
    expect(page.get_by_text("De boot is vastgelegd.")).to_be_visible()


def test_boot_voor_een_oud_lid_vastleggen_een_plaats_geven_en_wachtlijst_geweigerd(page):
    oud = oud_lid_binnen_de_termijn()
    wachtwoord_instellen(page, "oudlid")
    boot, tweede = f"Oudlid {STEMPEL}", f"Oudwacht {STEMPEL}"
    code = rek_met_plaats(page, reknaam("oud"), ["Kajak"])

    boot_vastleggen_voor_oud_lid(page, boot, oud["lidnummer"])
    expect(page.locator("dl.bl-feiten")).to_contain_text(oud["naam"])
    keuze = page.locator("#plaats option", has_text=code).get_attribute("value")
    page.get_by_label("Vrije plaats voor kajak").select_option(value=keuze)
    page.get_by_role("button", name="Wijs toe aan plek").click()
    expect(page.get_by_text("De boot heeft de plaats gekregen.")).to_be_visible()
    expect(page.get_by_role("link", name=code, exact=True)).to_be_visible()

    page.goto("/opgezegd")  # besluit 6: een boot van een oud-lid met een plaats staat hier
    rij = page.locator("main ul.bl-lijst > li").filter(has=page.locator("[data-label='Plaats']", has_text=code))
    expect(rij.locator("[data-label='Boot']")).to_have_text(boot)

    boot_vastleggen_voor_oud_lid(page, tweede, oud["lidnummer"])
    expect(page.get_by_text("Een oud-lid kan niet op de wachtlijst.")).to_be_visible()
    expect(page.get_by_role("button", name="Op de wachtlijst zetten")).to_have_count(0)
    with page.expect_navigation():  # de server weigert ook zonder knop
        page.evaluate("""() => {
            const f = document.createElement("form");
            f.method = "post";
            f.action = location.pathname + "/wachtlijst";
            f.append(document.querySelector("input[name=csrf_token]").cloneNode());
            document.body.append(f);
            f.submit();
        }""")
    expect(page.get_by_text(f"De eigenaar van boot {tweede} is oud-lid. De boot kan niet op de wachtlijst.")).to_be_visible()
