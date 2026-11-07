"""Blok 3, deel A van het nieuwe ontwerp (issue #150): de lijsten Boten, Leden, Opgezegd, Gaan opzeggen
en Wachtlijst met zoeken en filters (BV-46, BV-60), en het log met een kop per dag. Gebruikersinvoer
blijft geëscapet."""

import re
from datetime import UTC, date, datetime, timedelta

import pytest

from app.domein import CLI, toewijzing, vandaag, wachtlijst
from app.models import Logregel, db
from app.web import dagkop
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot, soort
from tests.unit.test_overzichten_en_instellingen import opzeggen
from tests.unit.test_web import inloggen

XSS = "<b>x</b>"
GEESCAPET = "&lt;b&gt;x&lt;/b&gt;"


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def titels(tekst):
    """De titels (bootnaam, lidnaam of plaatscode) van de items in de lijst."""
    return re.findall(r'<a class="bl-item__titel"[^>]*>([^<]*)</a>', tekst)


def aantal(tekst):
    return re.search(r'<p class="bl-aantal">([^<]*)</p>', tekst).group(1)


# Boten


@pytest.fixture
def boten(ingelogd):
    anna, bert = lid("1001", "Anna Zwaan"), lid("1002", "Bert Fuut")
    boot(anna.id, "Kajak", "Zeemeeuw")
    boot(bert.id, "Surfski", "Reiger")
    boot(None, "Kajak", "Klipper")
    return ingelogd


def test_boten_zijn_een_lijst_met_aantal_en_zonder_filter_alle_boten(boten):
    tekst = boten.get("/boten").text
    assert "<table" not in tekst.split('<section class="log"')[0]
    assert titels(tekst) == ["Klipper", "Reiger", "Zeemeeuw"] and aantal(tekst) == "3 boten"
    assert titels(boten.get("/boten?zoek=&bootsoort=").text) == ["Klipper", "Reiger", "Zeemeeuw"]


def test_boten_zoeken_op_boot_of_eigenaar_zonder_op_hoofdletters_te_letten(boten):
    # Mutant: de eigenaar of de boot uit de voorwaarde halen valt op de eerste of de tweede assert.
    assert titels(boten.get("/boten?zoek=ZEEM").text) == ["Zeemeeuw"]
    assert titels(boten.get("/boten?zoek=fuut").text) == ["Reiger"]


def test_boten_zoeken_neemt_procent_en_liggend_streepje_letterlijk(boten):
    # Mutant: autoescape=True weghalen laat '%' alles vinden.
    for teken in ("%", "_"):
        tekst = boten.get(f"/boten?zoek={teken}").text
        assert titels(tekst) == [] and "Geen boten gevonden." in tekst and "bl-aantal" not in tekst


def test_boten_filteren_op_bootsoort(boten):
    # Mutant: het filter op bootsoort weghalen geeft ook Reiger en valt hier.
    tekst = boten.get(f"/boten?bootsoort={soort('Kajak')}").text
    assert titels(tekst) == ["Klipper", "Zeemeeuw"] and aantal(tekst) == "2 boten"
    assert f'<option value="{soort("Kajak")}" selected>' in tekst
    assert titels(boten.get(f"/boten?bootsoort={soort('Kajak')}&zoek=klip").text) == ["Klipper"]


@pytest.mark.parametrize("waarde,verwacht", [("99999", []), ("abc", ["Klipper", "Reiger", "Zeemeeuw"]),
                                             ("99999999999", ["Klipper", "Reiger", "Zeemeeuw"])])
def test_boten_met_onbekende_of_ongeldige_bootsoort_geeft_geen_fout(boten, waarde, verwacht):
    # Zoals /vrij: een onbekende soort filtert alles weg, een waarde die geen getal is wordt genegeerd.
    r = boten.get(f"/boten?bootsoort={waarde}")
    assert r.status_code == 200 and titels(r.text) == verwacht


def test_een_boot_is_een_boot_en_een_lege_lijst_zegt_waarom(ingelogd):
    assert "Er zijn nog geen boten." in ingelogd.get("/boten").text
    boot(None, "Kajak", "Klipper")
    assert aantal(ingelogd.get("/boten").text) == "1 boot"


def test_boten_zoekterm_en_namen_komen_geescapet_terug(ingelogd):
    # Mutant: |safe op de zoekterm of op de bootnaam valt hier.
    boot(lid("1001", "Anna").id, "Kajak", XSS)
    tekst = ingelogd.get(f"/boten?zoek={XSS}").text
    assert XSS not in tekst and f'value="{GEESCAPET}"' in tekst
    assert XSS not in ingelogd.get("/boten").text and GEESCAPET in ingelogd.get("/boten").text


def test_nieuwe_boot_en_log_zijn_dichte_uitklapblokken(boten):
    tekst = boten.get("/boten").text
    assert '<summary id="nieuw-kop">Nieuwe boot</summary>' in tekst
    assert '<summary id="log-kop">Log</summary>' in tekst
    assert "<details open" not in tekst and "<details class=\"dj-disclosure\" open" not in tekst


# Leden


def test_leden_zijn_een_lijst_met_status_en_zoeken_met_aantal(ingelogd):
    lid("1001", "Anna Zwaan", lid_sinds=date(2015, 3, 12))
    lid("1002", "Bert Fuut")
    tekst = ingelogd.get("/leden").text
    assert titels(tekst) == ["Anna Zwaan", "Bert Fuut"] and aantal(tekst) == "2 leden"
    assert 'Lidnummer <span data-label="Lidnummer">1001</span> · lid sinds <span data-label="Lid sinds">12-03-2015</span>' in tekst
    assert '<span class="ds-tag" data-label="Status">lid</span>' in tekst
    gevonden = ingelogd.get("/leden?zoek=1002").text
    assert titels(gevonden) == ["Bert Fuut"] and aantal(gevonden) == "1 lid"
    assert "Geen leden gevonden." in ingelogd.get("/leden?zoek=zzz").text


def test_leden_zoekterm_komt_geescapet_terug(ingelogd):
    tekst = ingelogd.get(f"/leden?zoek={XSS}").text
    assert XSS not in tekst and f'value="{GEESCAPET}"' in tekst


def test_leden_import_is_een_dicht_uitklapblok(ingelogd):
    tekst = ingelogd.get("/leden").text
    assert '<summary id="import-kop">Import</summary>' in tekst and "<details open" not in tekst
    assert 'section class="log"' not in tekst  # Leden heeft geen log


# Opgezegd en Gaan opzeggen


@pytest.fixture
def opzeggers(ingelogd):
    """Twee oud-leden en twee leden die gaan opzeggen, elk met een boot op een plaats."""
    namen = [("Oud Een", "Kievit", "B/1/1", -30), ("Oud Twee", "Wolk", "B/1/2", -10),
             ("Gaat Een", "Fuut", "B/1/3", 30), ("Gaat Twee", XSS, "B/1/4", 60)]
    for n, (lidnaam, bootnaam, code, dagen) in enumerate(namen):
        eigenaar = lid(str(n), lidnaam)
        toewijzing.toewijzen(plaats(code, [soort("Kajak")]).id, boot(eigenaar.id, naam=bootnaam).id, CLI)
        opzeggen(eigenaar.id, opzegdatum=vandaag() + timedelta(days=dagen))
    return ingelogd


def test_opgezegd_is_een_lijst_zonder_rek_en_zoekt_op_boot_of_oud_lid(opzeggers):
    tekst = opzeggers.get("/opgezegd").text
    assert titels(tekst) == ["B/1/1", "B/1/2"] and aantal(tekst) == "2 plaatsen"
    assert 'data-label="Rek"' not in tekst and "Rek" not in tekst.split("<main")[1].split("</main>")[0]
    # Mutant: boot of lid uit de voorwaarde halen valt op de eerste of de tweede assert.
    assert titels(opzeggers.get("/opgezegd?zoek=kievit").text) == ["B/1/1"]
    gevonden = opzeggers.get("/opgezegd?zoek=oud+twee").text
    assert titels(gevonden) == ["B/1/2"] and aantal(gevonden) == "1 plaats"
    assert "Geen plaatsen gevonden." in opzeggers.get("/opgezegd?zoek=fuut").text
    assert titels(opzeggers.get("/opgezegd?zoek=%25").text) == []  # '%' is letterlijk


def test_opzeggend_is_een_lijst_zonder_rek_en_zoekt_op_boot_of_lid(opzeggers):
    tekst = opzeggers.get("/opzeggend").text
    assert titels(tekst) == ["Gaat Een", "Gaat Twee"] and aantal(tekst) == "2 boten"
    assert 'data-label="Rek"' not in tekst
    assert titels(opzeggers.get("/opzeggend?zoek=fuut").text) == ["Gaat Een"]
    assert titels(opzeggers.get("/opzeggend?zoek=gaat+twee").text) == ["Gaat Twee"]
    assert "Geen boten gevonden." in opzeggers.get("/opzeggend?zoek=kievit").text
    assert titels(opzeggers.get("/opzeggend?zoek=_").text) == []


@pytest.mark.parametrize("pad", ["/opgezegd", "/opzeggend"])
def test_opzeggers_zoekterm_en_bootnaam_komen_geescapet_terug(opzeggers, pad):
    tekst = opzeggers.get(f"{pad}?zoek={XSS}").text
    assert XSS not in tekst and f'value="{GEESCAPET}"' in tekst
    assert XSS not in opzeggers.get("/opzeggend").text and GEESCAPET in opzeggers.get("/opzeggend").text


def test_lege_lijsten_van_opzeggers_hebben_een_melding_met_rol(ingelogd):
    for pad, tekst in (("/opgezegd", "Er zijn geen plaatsen van opgezegde leden."),
                       ("/opzeggend", "Er zijn geen boten van leden die gaan opzeggen.")):
        assert f'<div class="ds-notice__body" role="status">{tekst}</div>' in ingelogd.get(pad).text


# Wachtlijst


@pytest.fixture
def wachters(ingelogd):
    for n, (lidnaam, bootnaam, bootsoort) in enumerate([
            ("Anna Zwaan", "Zwaluw", "Kajak"), ("Bert Fuut", "Reiger", "Surfski"),
            ("Cor Merel", XSS, "Kajak")]):
        wachtlijst.erop_zetten(boot(lid(str(n), lidnaam).id, bootsoort, bootnaam).id, "", CLI)
    return ingelogd


def test_wachtlijst_is_een_lijst_per_soort_met_aantal(wachters):
    tekst = wachters.get("/wachtlijst").text
    assert aantal(tekst) == "3 boten op de wachtlijst"
    assert re.findall(r"<h2 id=\"soort-\d+\">([^<]*)</h2>", tekst) == ["Kajak", "Surfski"]
    assert titels(tekst) == [GEESCAPET, "Zwaluw", "Reiger"]
    assert "Zwaluw van de lijst halen</button>" in tekst


def test_wachtlijst_zoeken_op_boot_of_lid(wachters):
    # Mutant: boot of lid uit de voorwaarde halen valt op de eerste of de tweede assert.
    assert titels(wachters.get("/wachtlijst?zoek=zwal").text) == ["Zwaluw"]
    gevonden = wachters.get("/wachtlijst?zoek=Bert").text
    assert titels(gevonden) == ["Reiger"] and aantal(gevonden) == "1 boot op de wachtlijst"
    assert "Geen boten gevonden." in wachters.get("/wachtlijst?zoek=zzz").text
    assert titels(wachters.get("/wachtlijst?zoek=%25").text) == []


def test_wachtlijst_filteren_op_bootsoort(wachters):
    # Mutant: het filter op bootsoort weghalen laat ook de surfski staan en valt hier.
    tekst = wachters.get(f"/wachtlijst?bootsoort={soort('Surfski')}").text
    assert titels(tekst) == ["Reiger"] and aantal(tekst) == "1 boot op de wachtlijst"
    assert f'<option value="{soort("Surfski")}" selected>' in tekst
    assert "Geen boten gevonden." in wachters.get("/wachtlijst?bootsoort=99999").text
    assert aantal(wachters.get("/wachtlijst?bootsoort=abc").text) == "3 boten op de wachtlijst"


def test_wachtlijst_zoekterm_en_bootnaam_komen_geescapet_terug(wachters):
    tekst = wachters.get(f"/wachtlijst?zoek={XSS}").text
    assert XSS not in tekst and f'value="{GEESCAPET}"' in tekst
    assert XSS not in wachters.get("/wachtlijst").text


def test_lege_wachtlijst_heeft_een_melding_met_rol(ingelogd):
    assert 'role="status">Er staan geen boten op de wachtlijst.</div>' in ingelogd.get("/wachtlijst").text


# Log


def logregel(tijdstip, **velden):
    db.session.add(Logregel(tijdstip=tijdstip, soort="mutatie", actor_soort="beheerder", actor_naam="Anna",
                            actie=velden.pop("actie", "boot.aangemaakt"), verwijzingen=["boot:1"], **velden))
    db.session.commit()


def dagen(tekst):
    """(kop, tijden) per dag, in de volgorde van de pagina."""
    return [(kop, re.findall(r'class="bl-logtijd"[^>]*>([^<]*)<', blok))
            for kop, blok in re.findall(r'<h2 class="bl-logdag__kop"><time[^>]*>([^<]*)</time></h2>(.*?)</ol>',
                                        tekst, re.DOTALL)]


def test_log_groepeert_per_lokale_dag_ook_rond_middernacht_en_de_utc_grens(ingelogd):
    # Amsterdam is in november UTC+1. 22:30 UTC is 23:30 op 5 november en 23:30 UTC is 00:30 op 6 november,
    # beide op 5 november in UTC. Mutant: groeperen op de UTC-datum voegt ze samen en valt hier.
    logregel(datetime(2026, 11, 4, 12, 0, tzinfo=UTC))
    logregel(datetime(2026, 11, 5, 22, 30, tzinfo=UTC))
    logregel(datetime(2026, 11, 5, 23, 30, tzinfo=UTC))
    assert dagen(ingelogd.get("/log").text) == [
        ("vrijdag 6 november 2026", ["00:30"]), ("donderdag 5 november 2026", ["23:30"]),
        ("woensdag 4 november 2026", ["13:00"])]


def test_log_zet_meerdere_mutaties_van_een_dag_onder_een_kop_nieuwste_eerst(ingelogd):
    logregel(datetime(2026, 11, 5, 8, 0, tzinfo=UTC))
    logregel(datetime(2026, 11, 5, 9, 15, tzinfo=UTC))
    logregel(datetime(2026, 11, 3, 9, 15, tzinfo=UTC))
    assert dagen(ingelogd.get("/log").text) == [
        ("donderdag 5 november 2026", ["10:15", "09:00"]), ("dinsdag 3 november 2026", ["10:15"])]


def test_log_toont_tijd_en_dag_ook_in_het_attribuut_in_lokale_tijd(ingelogd):
    logregel(datetime(2026, 11, 5, 23, 30, tzinfo=UTC))
    tekst = ingelogd.get("/log").text
    assert '<time datetime="2026-11-06">vrijdag 6 november 2026</time>' in tekst
    assert '<time class="bl-logtijd" datetime="2026-11-06T00:30">00:30</time>' in tekst


@pytest.mark.parametrize("dag,verwacht", [
    (date(2026, 11, 2), "maandag 2 november 2026"), (date(2026, 11, 3), "dinsdag 3 november 2026"),
    (date(2026, 11, 4), "woensdag 4 november 2026"), (date(2026, 11, 5), "donderdag 5 november 2026"),
    (date(2026, 11, 6), "vrijdag 6 november 2026"), (date(2026, 11, 7), "zaterdag 7 november 2026"),
    (date(2026, 11, 8), "zondag 8 november 2026"), (date(2027, 1, 1), "vrijdag 1 januari 2027"),
    (date(2026, 12, 31), "donderdag 31 december 2026")])
def test_dagkop_noemt_weekdag_en_maand_in_kleine_letters(dag, verwacht):
    assert dagkop(dag) == verwacht


def test_log_toont_gegevens_alleen_als_ze_er_zijn_en_escapet_ze(ingelogd):
    logregel(datetime(2026, 11, 5, 8, 0, tzinfo=UTC), gegevens={"naam": XSS, "soort": "Kajak"})
    logregel(datetime(2026, 11, 5, 9, 0, tzinfo=UTC), actie="boot.verwijderd")
    tekst = ingelogd.get("/log").text
    # Mutant: |safe op de gegevens of de actor valt hier.
    assert XSS not in tekst and f"naam: {GEESCAPET}; soort: Kajak" in tekst
    assert tekst.count('class="bl-loggeg"') == 1


def test_log_onder_een_overzicht_is_een_dicht_uitklapblok_en_op_de_logpagina_niet(ingelogd):
    logregel(datetime(2026, 11, 5, 8, 0, tzinfo=UTC))
    overzicht = ingelogd.get("/boten").text
    assert re.search(r'<details class="dj-disclosure">\s*<summary id="log-kop">Log</summary>', overzicht)
    assert "<details open" not in overzicht and 'dj-disclosure" open' not in overzicht
    for pad, kop in (("/log", "Mutatielog"), ("/log/techniek", "Technisch log")):
        pagina = ingelogd.get(pad).text
        assert f'<h1 id="log-kop">{kop}</h1>' in pagina
        assert "<details" not in pagina.split("<main")[1] and 'id="log-kop"' in pagina


def test_log_zonder_regels_zegt_dat_er_geen_mutaties_zijn(ingelogd):
    assert "<p>Nog geen mutaties.</p>" in ingelogd.get("/wachtlijst").text
