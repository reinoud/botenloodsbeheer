"""Rekindeling als CSV (issue #157), de route voor een mens: exporteren, in het bestand een plaats
en een omschrijving toevoegen, importeren, controleren in het rekoverzicht, en een fout bestand dat
geweigerd wordt zonder dat er iets verandert. Eigen rek met een naam die per run uniek is."""

from pathlib import Path

from conftest import reknaam, wachtwoord_instellen
from playwright.sync_api import expect
from test_loods import rek_aanmaken, sectie_van


def uploaden(page, tekst):
    page.goto("/indeling")
    page.set_input_files("#csv-bestand", {"name": "indeling.csv", "mimeType": "text/csv",
                                          "buffer": tekst.encode("utf-8")})
    page.get_by_role("button", name="Indeling importeren").click()


def test_csv_exporteren_aangepast_importeren_en_fout_bestand_geweigerd(page):
    wachtwoord_instellen(page, "rekindelingcsv")
    rek = reknaam("z")
    rek_aanmaken(page, rek, vakken=((1, 1), (1, 2)), omschrijving="Voor de import",
                 soorten={1: "Kajak"})

    page.goto("/indeling")
    with page.expect_download() as download:
        page.get_by_role("link", name="Indeling exporteren als CSV").click()
    export = Path(download.value.path()).read_text(encoding="utf-8-sig")
    assert f"{rek};Voor de import;1;1;Kajak;nee" in export and f"{rek};Voor de import;1;2;Kajak;nee" in export

    with page.expect_download() as sjabloon:
        page.get_by_role("link", name="Leeg sjabloon met uitleg downloaden").click()
    assert Path(sjabloon.value.path()).read_text(encoding="utf-8-sig").startswith("# Rekindeling")

    # Aangepast bestand: nieuwe omschrijving, een derde plaats en een extra bootsoort op vak 2.
    aangepast = (f"rek;omschrijving;verdieping;vak;bootsoorten;clubplaats\r\n"
                 f"{rek};Via CSV;1;1;Kajak;nee\r\n{rek};Via CSV;1;2;Kajak/Surfski;nee\r\n"
                 f"{rek};Via CSV;1;3;Surfski;ja\r\n")
    uploaden(page, aangepast)
    expect(page.get_by_text("Rekken: 0 nieuw, 1 gewijzigd. Plaatsen: 1 nieuw, 1 gewijzigd.")).to_be_visible()
    sectie = sectie_van(page, rek)
    expect(sectie).to_contain_text("Via CSV")
    expect(sectie.locator("tbody a")).to_have_text([f"{rek}/1/1", f"{rek}/1/2", f"{rek}/1/3"])
    page.get_by_role("link", name="Rekoverzicht", exact=True).click()
    sectie = sectie_van(page, rek)
    expect(sectie.locator("a.bl-vak")).to_have_count(3)
    expect(sectie.locator("a.bl-vak--leeg")).to_have_count(1)
    expect(sectie.get_by_role("img", name=f"Plaats {rek}/1/2, Kajak, Surfski, vrij")).to_be_visible()

    # Een fout bestand: elke foute regel met nummer en reden, en de indeling blijft zoals ze was.
    uploaden(page, f"rek;omschrijving;verdieping;vak;bootsoorten;clubplaats\r\n"
                   f"{rek};Fout;1;1;Kajak;nee\r\n{rek};Fout;1;5;Zeilboot;nee\r\n")
    alert = page.get_by_role("alert")
    expect(alert).to_contain_text("Het bestand is niet geïmporteerd. Er is niets veranderd.")
    expect(alert).to_contain_text("Regel 3: de bootsoort Zeilboot bestaat niet.")
    expect(alert).to_contain_text(f"Regel 2: rek {rek}: Verdieping 1 heeft een gat")
    page.get_by_role("link", name="Rekoverzicht", exact=True).click()
    sectie = sectie_van(page, rek)
    expect(sectie.locator("a.bl-vak")).to_have_count(3)
    page.goto("/indeling")
    expect(sectie_van(page, rek)).to_contain_text("Via CSV")
