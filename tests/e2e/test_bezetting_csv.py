"""Bezetting als CSV (issue #158), de route voor een mens: exporteren, in het bestand een naam
verkeerd spellen, een nieuwe boot toevoegen en een bezette plaats overschrijven, importeren, in het
koppelscherm het juiste lid kiezen, bevestigen, controleren op de plaatspagina en opnieuw
importeren: de koppeling is onthouden. Eigen rek met een naam die per run uniek is."""

import re
from pathlib import Path

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import boot_vastleggen, plaats_instellen, rek_aanmaken, toewijzen

KOP = "plaats;boot;bootsoort;eigenaar;lidnummer"


def uploaden(page, tekst):
    page.goto("/import-export")
    page.set_input_files("#bezetting-bestand", {"name": "bezetting.csv", "mimeType": "text/csv",
                                                "buffer": tekst.encode("utf-8")})
    page.get_by_role("button", name="Bezetting uploaden", exact=True).click()


def leden_uit_de_lijst(page):
    """(naam, lidnummer) van de eerste twee leden in de keuzelijst van /boten."""
    page.goto("/boten")
    teksten = page.locator("#eigenaar option").all_text_contents()[2:4]  # het blok Nieuwe boot is dicht; na 'Kies' en de vereniging
    return [re.fullmatch(r"(.+) \((\w+)\)", t).groups() for t in teksten]


def regel(page, tekst):
    return page.get_by_role("row").filter(has_text=tekst)


def test_bezetting_exporteren_aangepast_importeren_koppelen_en_opnieuw_importeren(page):
    wachtwoord_instellen(page, "bezettingcsv")
    rek = reknaam("t")
    (naam1, nr1), (_naam2, nr2) = leden_uit_de_lijst(page)
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2), (1, 3), (1, 4)), soorten={1: "Kajak"})
    plaats_instellen(page, f"{rek}/1/4", [], club=True)
    boot_vastleggen(page, f"Reiger {rek}", "Kajak", eigenaar_index=2)
    boot_vastleggen(page, f"Kievit {rek}", "Kajak", eigenaar_index=2)
    boot_vastleggen(page, f"Meeuw {rek}", "Kajak", eigenaar_index=3)
    boot_vastleggen(page, f"Clubkajak {rek}", "Kajak")
    toewijzen(page, f"{rek}/1/1", f"Reiger {rek}")
    toewijzen(page, f"{rek}/1/3", f"Kievit {rek}")
    toewijzen(page, f"{rek}/1/4", f"Clubkajak {rek}")

    page.goto("/import-export")
    with page.expect_download() as download:
        page.get_by_role("link", name="Bezetting exporteren als CSV").click()
    export = Path(download.value.path()).read_text(encoding="utf-8-sig")
    assert f"{rek}/1/1;Reiger {rek};Kajak;{naam1};{nr1}" in export
    assert f"{rek}/1/4;Clubkajak {rek};Kajak;clubboot;" in export
    with page.expect_download() as sjabloon:
        page.get_by_role("link", name="Leeg bezettingssjabloon met uitleg downloaden").click()
    assert Path(sjabloon.value.path()).read_text(encoding="utf-8-sig").startswith("# Bezetting")

    # Aangepast: een spelfout in de eigenaar, een nieuwe boot, een bezette plaats overschreven.
    spelfout = f"{naam1} {rek}"
    bestand = "\r\n".join([
        KOP, f"{rek}/1/1;Reiger {rek};Kajak;{spelfout};", f"{rek}/1/2;Fuut {rek};Kajak;;{nr2}",
        f"{rek}/1/3;Meeuw {rek};Kajak;;{nr2}", f"{rek}/1/4;Clubkajak {rek};Kajak;clubboot;"]) + "\r\n"
    uploaden(page, bestand)
    expect(page.get_by_role("heading", name="Bezetting importeren", exact=True)).to_be_visible()
    expect(regel(page, f"Reiger {rek}")).to_contain_text("te koppelen")
    expect(regel(page, f"Fuut {rek}")).to_contain_text("nieuwe boot")
    expect(regel(page, f"Meeuw {rek}")).to_contain_text("overschrijven")
    expect(regel(page, f"Meeuw {rek}")).to_contain_text(f"Kievit {rek} gaat van de plaats.")
    expect(regel(page, f"Clubkajak {rek}")).to_contain_text("ongewijzigd")
    expect(page.get_by_role("button", name="Bezetting importeren", exact=True)).to_be_disabled()
    for breedte in (1100, 360):
        page.set_viewport_size({"width": breedte, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), breedte

    # Het juiste lid kiezen en opslaan: de regel is nu in orde en bevestigen kan.
    regel(page, f"Reiger {rek}").get_by_label("Keuze voor regel 2").select_option(
        label=f"{naam1} ({nr1})")
    page.get_by_role("button", name="Keuzes opslaan").click()
    expect(page.get_by_text("De keuzes zijn opgeslagen.")).to_be_visible()
    expect(regel(page, f"Reiger {rek}")).to_contain_text("ongewijzigd")
    page.goto("/import-export")  # de lopende import staat in een blok op deze pagina
    expect(page.get_by_text("Er loopt een bezettingsimport")).to_be_visible()
    page.get_by_role("link", name="Bekijk het overzicht").click()
    page.get_by_role("button", name="Bezetting importeren", exact=True).click()
    expect(page.get_by_text("De bezetting is geïmporteerd. Nieuwe boten: 1, toegewezen: 0, "
                            "overschreven: 1, verplaatst: 0, ongewijzigd: 2, overgeslagen: 0.")).to_be_visible()

    # Na het bevestigen sta je weer op Import/export; de plaatsen staan op Indeling.
    expect(page).to_have_url(re.compile(r"/import-export$"))
    page.goto("/indeling")
    # Controleren op de plaatspagina's en in het log van de bootmutaties.
    page.get_by_role("link", name=f"{rek}/1/2", exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_contain_text(f"{rek}/1/2")
    expect(page.get_by_text(f"Fuut {rek}").first).to_be_visible()
    page.goto("/indeling")
    page.get_by_role("link", name=f"{rek}/1/3", exact=True).click()
    expect(page.get_by_text(f"Meeuw {rek}").first).to_be_visible()
    page.locator("summary", has_text="Log").click()  # het log is een dicht uitklapblok
    expect(page.get_by_text("plaats.vrijgegeven").first).to_be_visible()
    page.goto("/boten")
    kievit = page.locator("main > ul.bl-lijst > li").filter(has=page.get_by_role("link", name=f"Kievit {rek}", exact=True))
    expect(kievit).to_contain_text("geen plaats")  # Kievit is overschreven en heeft geen plaats meer

    # Opnieuw importeren: de koppeling is onthouden, dus geen enkele regel is nog te koppelen.
    uploaden(page, bestand)
    expect(page.get_by_text("Alle regels zijn in orde.")).to_be_visible()
    expect(regel(page, f"Reiger {rek}")).to_contain_text("ongewijzigd")
    expect(page.get_by_text("te koppelen", exact=True)).to_have_count(0)
    page.get_by_role("button", name="Import annuleren").click()
    expect(page.get_by_text("De import is geannuleerd.")).to_be_visible()
    expect(page).to_have_url(re.compile(r"/import-export$"))
    expect(page.get_by_text("Er loopt een bezettingsimport")).to_have_count(0)

    # De onthouden koppeling staat op haar scherm en gaat weg met de knop.
    page.get_by_role("link", name="Onthouden koppelingen").click()
    rij = page.get_by_role("row").filter(has_text=spelfout)
    expect(rij).to_contain_text(naam1)
    rij.get_by_role("button", name="Koppeling verwijderen").click()
    expect(page.get_by_text("De koppeling is verwijderd.")).to_be_visible()
    expect(page.get_by_text(spelfout)).to_have_count(0)
