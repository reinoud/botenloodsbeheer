"""Een lid kiezen met zoeken en een tussenstap (#295, BV-85 en BV-86): het zoeken zelf (domein) en de vier
schermen waar een beheerder een lid kiest: de bezettingsimport, Nieuwe boot, Boot wijzigen en Boten zonder
eigenaar. Elke test noemt de mutant die hem laat falen. Een oud-lid binnen de bewaartermijn is een treffer
bij de drie schermen met één keuze (#298, test_oud_lid_boot.py); de bezettingsimport toont en accepteert
nooit een oud-lid."""

import html
import re
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.domein import leden, lidkeuze, vandaag
from app.models import Bezettingsimport, Boot, db
from tests.unit.hulp import lid
from tests.unit.test_bezetting_csv import bestand, plaats
from tests.unit.test_bezetting_csv_web import cel, uploaden
from tests.unit.test_indeling_en_toewijzing import boot
from tests.unit.test_overzichten_en_instellingen import opzeggen
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture

# Domein


def leden_met_naam(aantal, naam="Zandstra"):
    return [lid(f"{2000 + i}", f"{naam} {i:02d}") for i in range(aantal)]


def test_zoeken_op_deel_van_de_naam_en_op_het_lidnummer(app):
    # Mutant: alleen op naam (of alleen op lidnummer) zoeken valt op de ene of de andere assert.
    anna, bram = lid("1001", "Anna Wielinga"), lid("1002", "Bram Kuiperberg")
    assert [t.lid for t in lidkeuze.veld("wieling").treffers] == [anna]
    assert [t.lid for t in lidkeuze.veld("1002").treffers] == [bram]
    assert [t.waarde for t in lidkeuze.veld("10").treffers] == ["1001", "1002"]  # waarde is het lidnummer


def test_minder_dan_twee_tekens_geeft_een_foutregel_zonder_te_zoeken(app):
    # Mutant: MIN_TEKENS 1 laat "a" Anna vinden; "  a " telt na het trimmen als een teken.
    lid("1001", "Anna")
    for term in ("", "a", "  a ", " "):
        v = lidkeuze.veld(term)
        assert v.treffers == [] and v.fout == lidkeuze.TE_KORT, term


def test_zonder_treffer_geeft_een_foutregel_die_zegt_wat_te_zoeken(app):
    lid("1001", "Anna")
    v = lidkeuze.veld("Zonder")
    assert (v.treffers, v.gekozen, v.meer) == ([], "", False)
    assert v.fout == "Geen lid gevonden. Zoek op een deel van de naam of op het lidnummer."


def test_hooguit_tien_treffers_en_dan_de_hint(app):
    # Mutant: grens 11, of `meer` niet zetten, valt hier; precies 10 geeft geen hint.
    leden_met_naam(11)
    v = lidkeuze.veld("Zandstra")
    assert len(v.treffers) == 10 and v.meer and v.gekozen == ""
    assert [t.lid.naam for t in v.treffers] == [f"Zandstra {i:02d}" for i in range(10)]  # op naam
    lid("3000", "Ander")
    assert not lidkeuze.veld("Zandstra 0").meer
    precies_tien = lidkeuze.veld("Zandstra 0")
    assert len(precies_tien.treffers) == 10 and not precies_tien.meer


def test_precies_een_treffer_staat_al_gekozen_en_meer_treffers_niet(app):
    # Mutant: nooit voorkiezen, of altijd de eerste voorkiezen, valt op een van beide.
    lid("1001", "Anna Wielinga"), lid("1002", "Bram Wielinga")
    assert lidkeuze.veld("Anna").gekozen == "1001"
    assert lidkeuze.veld("Wielinga").gekozen == ""


def test_een_eerder_gekozen_rondje_blijft_alleen_gekozen_als_het_nog_een_treffer_is(app):
    # Mutant: de keuze altijd houden valt op de tweede assert (een nieuwe term met een oude keuze).
    lid("1001", "Anna Wielinga"), lid("1002", "Bram Wielinga"), lid("1003", "Carola Zand")
    assert lidkeuze.veld("Wielinga", keuze="1002").gekozen == "1002"
    assert lidkeuze.veld("Wielinga", keuze="1003").gekozen == ""
    assert lidkeuze.veld("Carola", keuze="1002").gekozen == "1003"  # de enige treffer staat gekozen


def test_de_clubboot_is_een_treffer_bij_de_term_clubboot_en_anders_niet(app):
    # Mutant: de clubboot altijd tonen, of nooit, valt op de eerste of de tweede assert.
    lid("1001", "Anna Clubboot")
    v = lidkeuze.veld("clubboot")
    assert [t.waarde for t in v.treffers] == ["clubboot", "1001"] and v.treffers[0].lid is None
    assert [t.waarde for t in lidkeuze.veld("Anna").treffers] == ["1001"]
    assert lidkeuze.veld("CLUBBOOT").treffers[0].waarde == "clubboot"
    assert lidkeuze.veld("clubboot", club=False).treffers[0].waarde == "1001"


def test_het_veld_met_naam_en_lidnummer_zoekt_op_dat_lidnummer(app):
    # Het veld Eigenaar van een bestaande boot is "Naam (lidnummer)"; zoeken daarop moet iets vinden.
    anna = lid("1001", "Anna de Vries")
    assert [t.lid for t in lidkeuze.veld("Anna de Vries (1001)").treffers] == [anna]
    assert [t.waarde for t in lidkeuze.veld("Botenloods (clubboot)").treffers] == ["clubboot"]


def test_een_oud_lid_is_geen_kiesbaar_lid(app):
    # Mutant: zoeken en lid_van_waarde over alle leden valt hier. #298 breidt kiesbare_leden uit.
    lid("1001", "Anna Actief")
    oud = lid("1002", "Anna Oud", opzegdatum=vandaag())
    assert [t.waarde for t in lidkeuze.veld("Anna").treffers] == ["1001"]
    assert lidkeuze.lid_van_waarde(oud.lidnummer) is None and lidkeuze.lid_van_waarde("1001") is not None
    assert lidkeuze.lid_van_waarde("100") is None  # alleen het hele lidnummer


def test_het_zoekteken_procent_en_underscore_zijn_letterlijk(app):
    lid("1001", "Anna")
    assert lidkeuze.veld("%%").fout == lidkeuze.GEEN_LID and lidkeuze.veld("A_").fout == lidkeuze.GEEN_LID


# eigenaar(): wat een formulier met één keuze betekent


def test_eigenaar_rondje_lidnummer_clubboot_en_onbekende_waarde(app):
    anna = lid()
    assert lidkeuze.eigenaar("1001", "") == ((anna.id, False), None)
    assert lidkeuze.eigenaar("clubboot", "") == ((None, True), None)
    for onbekend in ("9999", str(anna.id), "club", "onbekend"):  # een id of oud woord is geen lidnummer
        waarde, veld = lidkeuze.eigenaar(onbekend, "Anna")
        assert waarde is None and veld.fout == lidkeuze.ONGELDIG and veld.term == "Anna", onbekend


def test_eigenaar_leeg_is_onbekend_behalve_bij_een_lid_of_oud_lid(app):
    anna = lid()
    assert lidkeuze.eigenaar("", "") == ((None, False), None)
    van_lid, van_club, onbekend = boot(anna.id, "Kajak", "Lid"), boot(None, "Kajak", "Club"), boot(None, "Kajak", "Wulp", onbekend=True)
    assert lidkeuze.eigenaar("", "", van_lid)[1].fout == lidkeuze.EIGENAAR_LEEG
    assert lidkeuze.eigenaar("", "", van_club) == ((None, False), None)  # #233
    assert lidkeuze.eigenaar("", "", onbekend) == ((None, False), None)


def test_eigenaar_het_ongewijzigde_veld_van_een_boot_laat_de_eigenaar_staan_een_andere_term_niet(app):
    anna = lid()
    b = boot(anna.id, "Kajak", "Lid")
    assert lidkeuze.eigenaar("", "Anna de Vries (1001)", b, "Anna de Vries (1001)") == ((anna.id, False), None)
    waarde, veld = lidkeuze.eigenaar("", "Anna", b, "Anna de Vries (1001)")
    assert waarde is None and veld.fout == lidkeuze.NIET_GEKOZEN
    assert lidkeuze.eigenaar("", "Anna", None)[1].fout == lidkeuze.NIET_GEKOZEN  # Nieuwe boot


LANG = "Maria Theresia (Tessa) van der Berg-Oostenrijk en Hongarije, echtgenote van Franz Stephan Josef"  # 95 tekens
assert len(LANG) == 95


def test_een_lidnaam_van_95_tekens_met_haakjes_overleeft_de_zoekterm_van_het_eigenaarveld(app):
    # Mutant: schoon() zonder MAX_TEKENS van lidkeuze kapt het lidnummer af (#316).
    maria = lid("1001", LANG)
    tekst = f"{LANG} ({maria.lidnummer})"
    assert len(tekst) > 100
    assert lidkeuze.veld(tekst).gekozen == "1001"
    b = boot(maria.id, "Kajak", "Fuut")
    assert lidkeuze.eigenaar("", tekst, b, tekst) == ((maria.id, False), None)


# De bezettingsimport


def keuzes():
    db.session.expire_all()
    return db.session.scalar(select(Bezettingsimport)).keuzes


def start_import(ingelogd, *regels):  # noqa: F811
    for code in sorted({r.split(";")[0] for r in regels}):
        plaats(code)
    uploaden(ingelogd, bestand(*regels))


def zoek(ingelogd, **data):  # noqa: F811
    return ingelogd.post("/bezetting/import/koppelen", data={"actie": "zoeken", **data})


def test_zoeken_bij_de_import_toont_treffers_als_rondjes_met_het_lidnummer_als_waarde(ingelogd):  # noqa: F811
    # Mutant: de database-id als waarde, een select, of geen legend valt hier.
    lid("1001", "Anna Wielinga"), lid("1002", "Bram Wielinga")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Wielinga;")
    r = zoek(ingelogd, **{"zoek-2": "Wielinga"})
    c = cel(r.text, 2)
    assert r.status_code == 200 and re.search(r'<legend>Treffers voor regel 2</legend>', c)
    assert re.findall(r'<input type="radio" id="zoek-2-t\d" name="keuze-2" value="(\d+)">', c) == ["1001", "1002"]
    assert "Anna Wielinga (1001)</label>" in c and "Bram Wielinga (1002)</label>" in c
    assert 'value="Wielinga"' in c and "<select" not in c and " checked" not in c.replace('name="overslaan-2"', "")


def test_de_zoekterm_en_de_naam_uit_het_bestand_staan_geescaped_in_het_zoekveld(ingelogd):  # noqa: F811
    # Mutant: |safe op de term of een treffer valt hier.
    lid("1001", "Anna <b>x</b>")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;<b>x</b>;")
    tekst = ingelogd.get("/bezetting/import").text
    assert 'value="&lt;b&gt;x&lt;/b&gt;"' in cel(tekst, 2) and "<b>x</b>" not in tekst
    r = zoek(ingelogd, **{"zoek-2": "<b>x</b>"})
    assert "<b>x</b>" not in r.text and "Anna &lt;b&gt;x&lt;/b&gt; (1001)</label>" in r.text


def test_zoeken_bij_de_import_met_een_kort_veld_geeft_aria_invalid_en_een_foutregel(ingelogd):  # noqa: F811
    lid()
    start_import(ingelogd, "A/1/1;Reiger;Kajak;X;")
    c = cel(zoek(ingelogd, **{"zoek-2": "a"}).text, 2)
    assert 'aria-invalid="true" aria-describedby="zoek-2-fout"' in c
    assert f'<span class="ds-field__error" id="zoek-2-fout">{lidkeuze.TE_KORT}</span>' in c


def test_zonder_treffer_bij_de_import_geeft_aria_invalid_en_een_foutregel(ingelogd):  # noqa: F811
    # Mutant: geen aria-invalid, of de foutregel niet koppelen met aria-describedby, valt hier.
    lid()
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Zonder;")
    c = cel(zoek(ingelogd, **{"zoek-2": "Zonder"}).text, 2)
    assert 'aria-invalid="true" aria-describedby="zoek-2-fout"' in c
    assert f'<span class="ds-field__error" id="zoek-2-fout">{lidkeuze.GEEN_LID}</span>' in c
    assert "<fieldset" not in c


def test_meer_dan_tien_treffers_bij_de_import_toont_er_tien_en_de_hint(ingelogd):  # noqa: F811
    leden_met_naam(11)
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Zandstra;")
    c = cel(zoek(ingelogd, **{"zoek-2": "Zandstra"}).text, 2)
    assert c.count('type="radio"') == 10
    assert re.search(r'<fieldset class="dj-choices" aria-describedby="zoek-2-meer">', c)
    assert '<p class="ds-field__hint" id="zoek-2-meer">Meer dan 10 treffers. Zoek preciezer.</p>' in c


def test_precies_een_treffer_bij_de_import_staat_gekozen_en_wordt_pas_bij_opslaan_bewaard(ingelogd):  # noqa: F811
    lid("1001", "Anna Wielinga")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Wielinga;")
    c = cel(zoek(ingelogd, **{"zoek-2": "Wielinga"}).text, 2)
    assert re.search(r'name="keuze-2" value="1001" checked>', c)
    assert keuzes() == {}  # nog niet opgeslagen
    r = ingelogd.post("/bezetting/import/koppelen", data={"zoek-2": "Wielinga", "keuze-2": "1001"}, follow_redirects=True)
    assert '<span class="ds-tag">nieuwe boot</span>' in r.text


def test_de_clubboot_is_een_treffer_bij_de_term_clubboot_in_de_import(ingelogd):  # noqa: F811
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Onbekend;")
    c = cel(zoek(ingelogd, **{"zoek-2": "clubboot"}).text, 2)
    assert re.search(r'name="keuze-2" value="clubboot" checked><label[^>]*>Botenloods \(clubboot\)</label>', c)
    ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": "clubboot"})
    assert keuzes() == {"2": "club"}


def test_na_zoeken_noemt_een_melding_bovenaan_de_open_regels_met_links(ingelogd):  # noqa: F811
    # Mutant: de melding ook zonder Zoeken, een verkeerd aantal, of een link naar een regel met een keuze.
    lid("1001", "Anna Wielinga"), lid("1002", "Bram Wielinga"), lid("1003", "Carola Zand")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Wielinga;", "A/1/2;Fuut;Kajak;Carola;", "A/1/3;Meeuw;Kajak;Zonder;",
                 "A/1/4;Kluut;Kajak;Wielinga;")
    assert "nog een keuze nodig" not in ingelogd.get("/bezetting/import").text
    r = zoek(ingelogd, **{"zoek-2": "Wielinga", "zoek-3": "Carola", "zoek-4": "Zonder", "zoek-5": "Wielinga"})
    melding = re.search(r'<div class="ds-notice__body" role="status"><p>(3 regels hebben nog een keuze nodig:.*?)</p>', r.text)[1]
    assert melding == ('3 regels hebben nog een keuze nodig: <a href="#zoek-2">regel 2</a>, '
                       '<a href="#zoek-4">regel 4</a> en <a href="#zoek-5">regel 5</a>.')
    assert r.text.index("nog een keuze nodig") < r.text.index("<table")  # vóór de tabel
    assert 'id="zoek-2"' in r.text and 'id="zoek-4"' in r.text  # de links wijzen naar bestaande zoekvelden
    een = zoek(ingelogd, **{"zoek-2": "Wielinga", "zoek-3": "Carola", "zoek-4": "Zand", "zoek-5": "Wielinga"})
    assert "2 regels hebben nog een keuze nodig" in een.text
    alles = zoek(ingelogd, **{"zoek-2": "Anna", "zoek-3": "Carola", "zoek-4": "Zand", "zoek-5": "Bram"})
    assert "nog een keuze nodig" not in alles.text


def test_de_melding_noemt_een_enkele_regel_in_het_enkelvoud(ingelogd):  # noqa: F811
    lid()
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Zonder;")
    assert '1 regel heeft nog een keuze nodig: <a href="#zoek-2">regel 2</a>.' in zoek(ingelogd, **{"zoek-2": "Zonder"}).text


def test_een_rondje_dat_na_een_nieuwe_zoekterm_geen_treffer_meer_is_vervalt(ingelogd):  # noqa: F811
    # Mutant: de oude keuze opslaan terwijl de beheerder een andere term zocht valt hier.
    lid("1001", "Anna Wielinga"), lid("1002", "Bram Kuiperberg")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Onbekend;")
    ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": "1001"})
    assert keuzes() != {}
    zoek(ingelogd, **{"zoek-2": "Kuiperberg", "keuze-2": "1001"})
    assert keuzes() == {}


def test_een_opgeslagen_keuze_van_een_lid_met_een_lange_naam_blijft_na_zoeken_op_een_andere_regel(ingelogd):  # noqa: F811
    # Mutant: de term afkappen op 100 tekens laat de keuze vervallen (#316).
    maria = lid("1001", LANG)
    lid("1002", "Bram Kuiperberg")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Onbekend;", "A/1/2;Wulp;Kajak;Onbekend;")
    ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": "1001"})
    assert keuzes() == {"2": str(maria.id)}
    tekst = html.unescape(re.search(r'name="zoek-2"[^>]*value="([^"]*)"', ingelogd.get("/bezetting/import").text)[1])
    assert tekst == f"{LANG} (1001)"
    zoek(ingelogd, **{"zoek-2": tekst, "keuze-2": "1001", "zoek-3": "Kuiperberg"})
    assert keuzes() == {"2": str(maria.id)}


def test_een_vervalst_lidnummer_bij_de_import_wordt_geweigerd(ingelogd):  # noqa: F811
    # Mutant: een onbekende waarde stil negeren, of als id lezen, valt hier. Het lid-id van Anna is geen lidnummer.
    anna = lid("1001", "Anna")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Onbekend;")
    for waarde in ("9999", "abc", "club", str(anna.id), "overslaan", "1001 "):
        r = ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": waarde}, follow_redirects=True)
        assert lidkeuze.KEUZES_ONGELDIG in r.text, waarde
        assert keuzes() == {}, waarde


def test_een_oud_lid_wordt_bij_de_import_nooit_getoond_en_nooit_geaccepteerd(ingelogd):  # noqa: F811
    # BV-86: bij de import toont de server geen oud-leden. Mutant: over alle leden zoeken valt op de eerste
    # assert, de keuze niet controleren op de tweede.
    lid("1001", "Anna Actief")
    oud = lid("1002", "Anna Oud", opzegdatum=vandaag())
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Anna;")
    c = cel(zoek(ingelogd, **{"zoek-2": "Anna"}).text, 2)
    assert "Anna Actief (1001)" in c and "Anna Oud" not in c and "oud-lid" not in c and oud.lidnummer not in c
    r = ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": oud.lidnummer}, follow_redirects=True)
    assert lidkeuze.KEUZES_ONGELDIG in r.text
    assert keuzes() == {}


def test_een_zoekterm_voor_een_regel_buiten_de_import_wordt_genegeerd(ingelogd):  # noqa: F811
    lid()
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Onbekend;")
    r = zoek(ingelogd, **{"zoek-2": "Anna", "zoek-999": "Anna", "zoek-x": "Anna"})
    assert r.status_code == 200 and 'id="zoek-2"' in r.text and "zoek-999" not in r.text


def test_zoeken_zonder_lopende_import_verwijst_naar_import_export(ingelogd):  # noqa: F811
    r = ingelogd.post("/bezetting/import/koppelen", data={"actie": "zoeken", "zoek-2": "Anna"}, follow_redirects=True)
    assert r.request.path == "/import-export"


def test_het_vakje_overslaan_staat_op_elke_regel_met_een_keuzecel_en_de_lijsten_hebben_het_niet_meer(ingelogd):  # noqa: F811
    # Mutant: "Regel overslaan" als optie terug, of het vakje alleen bij de soortlijst, valt hier.
    lid()
    plaats("A/1/1", ("Kajak", "Surfski"))
    plaats("A/1/2")
    plaats("A/1/3")
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kayak;X;", "A/1/2;Fuut;Kajak;X;", "Z/9/9;Meeuw;Kajak;;", "A/1/3;Kluut;Kajak;;"))
    tekst = ingelogd.get("/bezetting/import").text
    for regel in (2, 3, 4):
        assert f'<input type="checkbox" id="over-{regel}" name="overslaan-{regel}"' in cel(tekst, regel), regel
    assert "overslaan-5" not in tekst  # een regel in orde heeft geen keuzecel
    assert 'value="overslaan"' not in tekst and "<option" in tekst and ">Regel overslaan</option>" not in tekst
    r = ingelogd.post("/bezetting/import/koppelen", data={"overslaan-3": "on", "overslaan-4": "on"}, follow_redirects=True)
    assert r.text.count('<span class="ds-tag">overgeslagen</span>') == 2
    assert 'name="overslaan-3" checked' in cel(r.text, 3)


# Nieuwe boot


def test_nieuwe_boot_na_zoeken_toont_de_treffers_houdt_de_invoer_en_slaat_niets_op(ingelogd):  # noqa: F811
    lid("1001", "Anna Wielinga"), lid("1002", "Bram Wielinga")
    r = ingelogd.post("/boten", data={"actie": "zoeken", "naam": "Fuut", "bootsoort": "2", "zoek": "Wielinga"})
    assert r.status_code == 200 and db.session.scalar(select(Boot)) is None
    assert '<details class="bl-nieuw" open>' in r.text and 'value="Fuut"' in r.text
    assert re.search(r'<option value="2" selected>', r.text) and 'value="Wielinga"' in r.text
    assert re.findall(r'<input type="radio" id="eigenaar-t\d" name="eigenaar" value="(\d+)"', r.text) == ["1001", "1002"]
    assert "<legend>Treffers voor Eigenaar</legend>" in r.text


def test_nieuwe_boot_zonder_treffer_geeft_aria_invalid_en_een_foutregel(ingelogd):  # noqa: F811
    lid()
    r = ingelogd.post("/boten", data={"actie": "zoeken", "naam": "Fuut", "bootsoort": "1", "zoek": "Zonder"})
    assert 'aria-invalid="true" aria-describedby="eigenaar-hint eigenaar-fout"' in r.text
    assert f'id="eigenaar-fout">{lidkeuze.GEEN_LID}</span>' in r.text


def test_nieuwe_boot_met_het_gekozen_rondje_en_de_clubboot(ingelogd):  # noqa: F811
    anna = lid()
    ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "zoek": "Anna", "eigenaar": "1001"})
    ingelogd.post("/boten", data={"naam": "Clubkajak", "bootsoort": "1", "zoek": "clubboot", "eigenaar": "clubboot"})
    boten = {b.naam: (b.lid_id, b.clubboot) for b in db.session.scalars(select(Boot))}
    assert boten == {"Fuut": (anna.id, False), "Clubkajak": (None, True)}


def test_nieuwe_boot_met_een_oud_lid_buiten_de_termijn_als_rondje_wordt_geweigerd(ingelogd):  # noqa: F811
    # BV-86 (#298): binnen de termijn is een oud-lid kiesbaar (test_oud_lid_boot.py). Mutant: lid_van_waarde
    # over alle leden.
    oud = lid("1002", "Oud", opzegdatum=leden.jaren_terug(vandaag(), leden.BEWAARJAREN) - timedelta(days=1))
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": oud.lidnummer})
    assert r.status_code == 422 and lidkeuze.ONGELDIG in r.text and db.session.scalar(select(Boot)) is None


def test_de_zoekterm_bij_nieuwe_boot_staat_geescaped(ingelogd):  # noqa: F811
    lid("1001", "Anna <b>x</b>")
    r = ingelogd.post("/boten", data={"actie": "zoeken", "naam": "<i>y</i>", "bootsoort": "1", "zoek": "<b>x</b>"})
    assert "<b>x</b>" not in r.text and "<i>y</i>" not in r.text
    assert 'value="&lt;b&gt;x&lt;/b&gt;"' in r.text and "Anna &lt;b&gt;x&lt;/b&gt; (1001)</label>" in r.text


# Boot wijzigen


def test_boot_wijzigen_na_zoeken_toont_de_treffers_en_het_blok_staat_open(ingelogd):  # noqa: F811
    lid("1001", "Anna Wielinga"), lid("1002", "Bram Wielinga")
    b = boot(None, "Kajak", "Wulp", onbekend=True)
    r = ingelogd.post(f"/boten/{b.id}", data={"actie": "zoeken", "naam": "Wulp 2", "bootsoort": b.bootsoort_id,
                                              "zoek": "Wielinga"})
    assert r.status_code == 200 and (b.naam, b.lid_id) == ("Wulp", None)
    assert re.search(r'<details class="dj-disclosure" open>\s*<summary id="wijzigen-kop">', r.text)
    assert 'value="Wulp 2"' in r.text
    assert re.findall(r'name="eigenaar" value="(\d+)"', r.text) == ["1001", "1002"]


def test_boot_wijzigen_met_een_ander_rondje_wisselt_de_eigenaar(ingelogd):  # noqa: F811
    anna, bram = lid(), lid("1002", "Bram")
    b = boot(anna.id, "Kajak", "Fuut")
    ingelogd.post(f"/boten/{b.id}", data={"naam": "Fuut", "bootsoort": b.bootsoort_id, "zoek": "Bram", "eigenaar": "1002"})
    assert b.lid_id == bram.id


def test_boot_wijzigen_met_een_andere_term_zonder_rondje_wijzigt_niets(ingelogd):  # noqa: F811
    # Mutant: de term als keuze lezen, of leeg als onbekend, valt hier.
    anna = lid()
    b = boot(anna.id, "Kajak", "Fuut")
    r = ingelogd.post(f"/boten/{b.id}", data={"naam": "Fuut 2", "bootsoort": b.bootsoort_id, "zoek": "Bram"})
    assert r.status_code == 422 and lidkeuze.NIET_GEKOZEN in r.text and (b.naam, b.lid_id) == ("Fuut", anna.id)


def test_boot_wijzigen_met_een_ongewijzigd_eigenaarveld_met_een_lange_lidnaam_laat_de_eigenaar_staan(ingelogd):  # noqa: F811
    # Mutant: de term afkappen op 100 tekens geeft de foutregel "Kies een lid uit de treffers" (#316).
    maria = lid("1001", LANG)
    b = boot(maria.id, "Kajak", "Fuut")
    veld = re.search(r'id="eigenaar" name="zoek"[^>]*value="([^"]*)"', ingelogd.get(f"/boten/{b.id}").text)[1]
    assert html.unescape(veld) == f"{LANG} (1001)"
    r = ingelogd.post(f"/boten/{b.id}", data={"naam": "Fuut 2", "bootsoort": b.bootsoort_id, "zoek": html.unescape(veld)})
    assert r.status_code < 400 and lidkeuze.NIET_GEKOZEN not in r.text and (b.naam, b.lid_id) == ("Fuut 2", maria.id)


@pytest.mark.parametrize("pad", ["/boten", "/boten/zonder-eigenaar"])
def test_geen_select_met_leden_op_de_schermen(ingelogd, pad):  # noqa: F811
    # Acceptatiecriterium: geen select met leden als opties. Mutant: de oude lijst terug valt hier.
    lid()
    boot(None, "Kajak", "Wulp", onbekend=True)
    tekst = ingelogd.get(pad).text
    assert "Anna de Vries" not in tekst and 'name="eigenaar"' not in tekst.replace('type="radio" name="eigenaar"', "")


# Zoeken laat de keuzes elders staan (#295, herstel)


def formulier(tekst):
    """Wat de browser bij Zoeken meestuurt: elk zoekveld en elk aangevinkt rondje."""
    data = {"actie": "zoeken"}
    data |= {n: w for n, w in re.findall(r'type="search" id="[^"]*" name="(zoek-\d+)"[^>]*value="([^"]*)"', tekst)}
    data |= {n: w for n, w in re.findall(r'type="radio" id="[^"]*" name="(keuze-\d+)" value="([^"]*)" checked', tekst)}
    return data


def zoek_elders(ingelogd, term="Bram"):  # noqa: F811
    """Zoekt op regel 3 met het formulier zoals regel 2 het toont na het opslaan van zijn keuze."""
    data = formulier(ingelogd.get("/bezetting/import").text)
    return ingelogd.post("/bezetting/import/koppelen", data=data | {"zoek-3": term})


def test_zoeken_elders_houdt_een_opgeslagen_keuze_die_niet_op_de_naam_uit_het_bestand_lijkt(ingelogd):  # noqa: F811
    # Mutant: de naam uit het bestand als zoekterm van een opgeslagen keuze valt hier.
    anna = lid("1001", "Anna de Vries")
    lid("1002", "Bram Jansen")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;S. de Vrees;", "A/1/2;Fuut;Kajak;Onbekend;")
    ingelogd.post("/bezetting/import/koppelen", data={"zoek-2": "Anna", "keuze-2": "1001"})
    assert 'value="Anna de Vries (1001)"' in ingelogd.get("/bezetting/import").text
    zoek_elders(ingelogd)
    assert keuzes().get("2") == str(anna.id)


def test_zoeken_elders_houdt_een_opgeslagen_clubboot(ingelogd):  # noqa: F811
    lid("1002", "Bram Jansen")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Onbekend;", "A/1/2;Fuut;Kajak;Onbekend;")
    ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": "clubboot"})
    assert "(clubboot)\"" in ingelogd.get("/bezetting/import").text
    zoek_elders(ingelogd)
    assert keuzes().get("2") == "club"


def test_zoeken_elders_houdt_een_opgeslagen_keuze_waarvan_het_lidnummer_in_meer_dan_tien_nummers_staat(ingelogd):  # noqa: F811
    # Herreview Sentinel: de begintekst "Naam (12)" zoekt op 12; dat staat ook in 112, 120..129 en 212.
    gekozen = lid("12", "Zwart")
    for nr in ("112", "120", "121", "122", "123", "124", "125", "126", "127", "128", "129", "212"):
        lid(nr, f"Aalders {nr}")
    lid("3000", "Bram Jansen")
    plaats("A/1/1")
    plaats("A/1/2")
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kajak;Zwart;", "A/1/2;Fuut;Kajak;Onbekend;"))
    ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": gekozen.lidnummer})
    assert keuzes().get("2") == str(gekozen.id), keuzes()
    data = formulier(ingelogd.get("/bezetting/import").text)
    assert data.get("keuze-2") == "12", data
    data["zoek-3"] = "Bram"
    ingelogd.post("/bezetting/import/koppelen", data=data)
    assert keuzes().get("2") == str(gekozen.id), keuzes()


def test_zoeken_elders_houdt_een_opgeslagen_keuze_buiten_de_eerste_tien_treffers(ingelogd):  # noqa: F811
    leden = leden_met_naam(12)
    lid("3000", "Bram Jansen")
    start_import(ingelogd, "A/1/1;Reiger;Kajak;Zandstra;", "A/1/2;Fuut;Kajak;Onbekend;")
    ingelogd.post("/bezetting/import/koppelen", data={"keuze-2": leden[-1].lidnummer})
    zoek_elders(ingelogd)
    assert keuzes().get("2") == str(leden[-1].id)


def test_zoeken_bewaart_de_soort_het_vakje_overslaan_en_de_rondjes_van_andere_regels(ingelogd):  # noqa: F811
    # Mutant: bij Zoeken koppelen overslaan valt op alle drie.
    from tests.unit.test_bezetting_csv import soort
    bram = lid("1002", "Bram Jansen")
    plaats("A/1/1", ("Kajak", "Surfski"))
    for code in ("A/1/2", "A/1/3", "A/1/4"):
        plaats(code)
    uploaden(ingelogd, bestand("A/1/1;Reiger;Kayak;;1002", "A/1/2;Fuut;Kajak;Onbekend;",
                               "A/1/3;Wulp;Kajak;Onbekend;", "A/1/4;Kievit;Kajak;Onbekend;"))
    s = str(soort("Surfski"))
    zoek(ingelogd, **{"soort-2": s, "keuze-3": "1002", "overslaan-4": "on", "zoek-5": "Bram"})
    assert keuzes() == {"soort-2": s, "3": str(bram.id), "overslaan-4": "1"}


def test_boot_wijzigen_toont_naam_en_lidnummer_ook_bij_een_oud_lid_en_zoeken_vindt_het_lid(ingelogd):  # noqa: F811
    oud = lid("1002", "Oud Lid")
    b = boot(oud.id, "Kajak", "Fuut")
    opzeggen(oud.id, opzegdatum=vandaag())
    veld = re.search(r'id="eigenaar" name="zoek"[^>]*value="([^"]*)"', ingelogd.get(f"/boten/{b.id}").text)[1]
    assert veld == "Oud Lid (1002)"  # geen "oud-lid" in de term
    anna = lid("1001", "Anna de Vries")
    veld = lidkeuze.veld(f"{anna.naam} ({anna.lidnummer})")  # het ongewijzigde veld van een lid
    assert [t.waarde for t in veld.treffers] == ["1001"] and veld.gekozen == "1001"


def test_nieuwe_boot_zegt_bij_het_fotoveld_dat_een_foto_na_zoeken_niet_bewaard_blijft(ingelogd):  # noqa: F811
    # Mutant: de hint of aria-describedby weglaten valt hier.
    html = ingelogd.get("/boten").text
    assert re.search(r'id="foto" name="foto" type="file"[^>]*aria-describedby="foto-hint"', html)
    assert '<p class="bl-hint" id="foto-hint">Kies de foto opnieuw; een foto blijft niet bewaard na Zoeken.</p>' in html
