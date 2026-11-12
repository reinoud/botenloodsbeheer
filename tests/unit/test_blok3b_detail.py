"""Blok 3, deel B van het nieuwe ontwerp (issue #150): het detail van Boot en Lid (2B, BV-46, BV-47, BV-60).
De feiten bovenaan, de taak die nu past, de rest in dichte uitklapblokken; gebruikersinvoer blijft geëscapet."""

import re

import pytest

from app.domein import CLI, toewijzing, vandaag, wachtlijst
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats, png
from tests.unit.test_blok3a_lijsten import GEESCAPET, XSS
from tests.unit.test_indeling_en_toewijzing import boot
from tests.unit.test_overzichten_en_instellingen import opzeggen
from tests.unit.test_web import inloggen


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def feiten(tekst):
    """De feiten van de pagina als {naam: waarde zonder opmaak}, in de volgorde van het scherm."""
    dl = re.search(r'<dl class="bl-feiten">(.*?)</dl>', tekst, re.DOTALL).group(1)
    return {k: re.sub(r"<[^>]+>", "", v).strip() for k, v in re.findall(r"<dt>([^<]*)</dt>\s*<dd>(.*?)</dd>", dl, re.DOTALL)}


def taak(tekst):
    return re.search(r'<section class="kaart bl-taak".*?</section>', tekst, re.DOTALL).group(0)


def oud_lid_boot():
    oud = lid("1003", "Oud Lid")
    b = boot(oud.id, naam="Oudje")
    opzeggen(oud.id, opzegdatum=vandaag())  # een opzegdatum van vandaag telt als oud-lid
    return b


# Menu (BV-47 punt 3)


def test_menu_markeert_boten_op_een_boot_en_leden_op_een_lid(ingelogd):
    # Mutant: de elif in base.html weghalen laat beide aanroepen zonder markering en valt hier.
    anna = lid()
    b = boot(anna.id)
    for pad, naam in ((f"/boten/{b.id}", "Boten"), (f"/leden/{anna.id}", "Leden")):
        tekst = ingelogd.get(pad).text
        assert re.findall(r'<a class="dj-nav__link" href="[^"]*" aria-current="true">([^<]*)</a>', tekst) == [naam], pad
        assert 'aria-current="page"' not in tekst, pad
    assert 'href="/boten" aria-current="page">Boten' in ingelogd.get("/boten").text  # het overzicht zelf blijft "page"


# Plaats: eigenaar (issue #234)


def eigenaar_blok(tekst):
    return re.search(r'<h2 class="dj-panel__title" id="eigenaar-kop">.*?</section>', tekst, re.DOTALL).group(0)


def test_plaats_linkt_de_naam_van_een_lid_en_een_oud_lid_naar_het_lid(ingelogd):
    # Mutant: de <a> in plaats.html weghalen valt op de eerste assert; "(oud-lid)" binnen de link zetten op de tweede.
    anna = lid()
    p = plaats("A/1/1")
    toewijzing.toewijzen(p.id, boot(anna.id).id, CLI)
    assert f'<dd data-veld="naam"><a href="/leden/{anna.id}">Anna de Vries</a></dd>' in eigenaar_blok(ingelogd.get(f"/plaatsen/{p.id}").text)
    oud, q = lid("1003", "Oud Lid"), plaats("A/1/2")
    toewijzing.toewijzen(q.id, boot(oud.id, naam="Oudje").id, CLI)
    opzeggen(oud.id, opzegdatum=vandaag())  # een opzegdatum van vandaag telt als oud-lid
    assert f'<a href="/leden/{oud.id}">Oud Lid</a> (oud-lid)</dd>' in eigenaar_blok(ingelogd.get(f"/plaatsen/{q.id}").text)


def test_plaats_laat_clubboot_en_onbekende_eigenaar_zonder_link(ingelogd):
    # Mutant: een link om "clubboot" of "onbekend" in plaats.html valt hier op de assert dat er geen /leden/ staat.
    for code, b in (("A/1/1", boot(None, naam="Club")), ("A/1/2", boot(None, naam="Wulp", onbekend=True))):
        p = plaats(code)
        toewijzing.toewijzen(p.id, b.id, CLI)
        blok = eigenaar_blok(ingelogd.get(f"/plaatsen/{p.id}").text)
        assert "/leden/" not in blok and "<a " not in blok


def test_plaats_geeft_de_naam_van_de_eigenaar_geescapet_terug(ingelogd):
    # Mutant: |safe op boot.lid.naam in plaats.html valt hier.
    x = lid(naam=XSS)
    p = plaats("A/1/1")
    toewijzing.toewijzen(p.id, boot(x.id).id, CLI)
    blok = eigenaar_blok(ingelogd.get(f"/plaatsen/{p.id}").text)
    assert XSS not in blok and f">{GEESCAPET}</a>" in blok


# Boot: feiten


def test_eigenaar_is_een_link_naar_het_lid_en_een_clubboot_heeft_geen_link(ingelogd):
    # Mutant: de link om de eigenaar weghalen valt op de eerste assert; de link bij een clubboot op de tweede.
    anna = lid()
    b, club = boot(anna.id), boot(None, naam="Clubkajak")
    tekst = ingelogd.get(f"/boten/{b.id}").text
    assert f'<dt>Eigenaar</dt> <dd><a href="/leden/{anna.id}">Anna de Vries</a></dd>' in tekst
    tekst = ingelogd.get(f"/boten/{club.id}").text
    assert re.search(r"<dt>Eigenaar</dt> <dd>[^<]*\(clubboot\)</dd>", tekst)


def test_feiten_volgorde_en_wachtlijst_alleen_zonder_plaats(ingelogd):
    p = plaats()
    met = boot(lid().id, naam="Bezetter")
    toewijzing.toewijzen(p.id, met.id, CLI)
    assert list(feiten(ingelogd.get(f"/boten/{met.id}").text)) == ["Bootsoort", "Eigenaar", "Plaats"]
    zonder = boot(lid("1002", "Bert Fuut").id, naam="Kievit")
    assert feiten(ingelogd.get(f"/boten/{zonder.id}").text) == {
        "Bootsoort": "Kajak", "Eigenaar": "Bert Fuut", "Plaats": "geen", "Wachtlijst": "nee"}
    wachtlijst.erop_zetten(zonder.id, "2024-03-01", CLI)
    assert feiten(ingelogd.get(f"/boten/{zonder.id}").text)["Wachtlijst"] == "sinds 01-03-2024"


def test_foto_staat_klein_bij_de_feiten_en_ontbreekt_zonder_foto(ingelogd):
    # Mutant: de voorwaarde op boot.afbeelding weghalen geeft een kapotte img zonder foto en valt op de tweede assert.
    met, zonder = boot(lid().id, foto=png()), boot(None, naam="Zonder")
    tekst = ingelogd.get(f"/boten/{met.id}").text
    assert re.search(r'<img class="bl-kopfoto" src="[^"]+" alt="Foto van Zeemeeuw" width="96" height="72">', tekst)
    assert "bl-kopfoto" not in ingelogd.get(f"/boten/{zonder.id}").text


# Boot: de taak


def test_taak_op_een_bezette_plaats_is_een_volledige_zin_met_link(ingelogd):
    # BV-60. Mutant: de zin of de link weglaten valt op de derde assert.
    p = plaats()
    b = boot(lid().id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert f'<h2 class="bl-taak__kop" id="taak-kop">Op plaats {p.code}</h2>' in t
    assert 'name="plaats_id"' not in t and "Op de wachtlijst zetten" not in t
    assert f'<p>Vrijgeven of verplaatsen doe je op de plaats. <a href="/plaatsen/{p.id}">Naar plaats {p.code}</a></p>' in t


def test_taak_zonder_plaats_heeft_toewijzen_en_wachtlijst_als_onderdelen(ingelogd):
    # BV-47 punt 5. Mutant: de wachtlijst uit de taak halen valt op de tweede assert.
    plaats()
    b = boot(lid().id)
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert '>Plaats toewijzen</h2>' in t and 'name="plaats_id"' in t and "Wijs toe aan plek" in t
    assert '<h3 class="bl-subkop">Wachtlijst</h3>' in t and "Op de wachtlijst zetten" in t


def test_taak_met_alleen_de_wachtlijst_als_er_geen_vrije_plaats_is(ingelogd):
    b = boot(lid().id)
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert "Er is geen vrije plaats voor kajak." in t and "Op de wachtlijst zetten" in t and 'name="plaats_id"' not in t


def test_taak_van_een_wachtende_boot_haalt_hem_van_de_lijst(ingelogd):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "2024-03-01", CLI)
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert "Zeemeeuw staat sinds 01-03-2024 op de wachtlijst voor kajak." in t and "Van de wachtlijst halen" in t
    assert "Op de wachtlijst zetten" not in t


def test_taak_van_een_clubboot_kent_geen_wachtlijst(ingelogd):
    plaats(club=True)
    b = boot(None)
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert "Vrije plaats voor kajak" in t and '<optgroup label="Clubplaatsen">' in t and "Een clubboot kan niet op de wachtlijst." in t
    assert "Op de wachtlijst zetten" not in t


def test_oud_lid_heeft_boot_verwijderen_als_taak_en_het_blok_heet_boot_wijzigen(ingelogd):
    # BV-47 punt 4. Mutant: de gevaarknop terug in het uitklapblok zetten valt op de tweede assert (dubbel) en de samenvatting op de derde.
    b = oud_lid_boot()
    tekst = ingelogd.get(f"/boten/{b.id}").text
    t = taak(tekst)
    assert '>Boot verwijderen</h2>' in t and "De eigenaar is oud-lid. De boot krijgt geen plaats en kan niet op de wachtlijst." in t
    assert tekst.count("Boot Oudje verwijderen") == 1 and "Boot Oudje verwijderen" in t
    assert '<summary id="wijzigen-kop">Boot wijzigen</summary>' in tekst and 'name="plaats_id"' not in tekst
    assert feiten(tekst)["Wachtlijst"] == "nee"


def test_oud_lid_met_een_boot_op_de_wachtlijst_ziet_dat_de_import_hem_eraf_haalt(ingelogd):
    # #176. Mutant: de tak boot.wachtlijst in de taak weglaten valt op de eerste assert.
    oud = lid("1003", "Oud Lid")
    b = boot(oud.id, naam="Oudje")
    wachtlijst.erop_zetten(b.id, "2024-03-01", CLI)
    opzeggen(oud.id, opzegdatum=vandaag())
    tekst = ingelogd.get(f"/boten/{b.id}").text
    t = taak(tekst)
    assert "De eigenaar is oud-lid. De boot krijgt geen plaats. Bij de volgende ledenimport gaat de boot van de wachtlijst." in t
    assert "kan niet op de wachtlijst" not in t and "Van de wachtlijst halen" not in t
    assert feiten(tekst)["Wachtlijst"] == "sinds 01-03-2024"


def test_oud_lid_met_een_boot_op_een_plaats_houdt_de_taak_op_plaats(ingelogd):
    # Toets bouw deel B (designsystem ce772e6): eerst gaat de plaats vrij. Mutant: verwijderen_in_taak = oud_lid valt op de assert op het blok.
    p = plaats()
    oud = lid("1003", "Oud Lid")
    b = boot(oud.id, naam="Oudje")
    toewijzing.toewijzen(p.id, b.id, CLI)
    opzeggen(oud.id, opzegdatum=vandaag())
    tekst = ingelogd.get(f"/boten/{b.id}").text
    assert f">Op plaats {p.code}</h2>" in taak(tekst)
    assert '<summary id="wijzigen-kop">Boot wijzigen of verwijderen</summary>' in tekst
    assert tekst.count("Boot Oudje verwijderen") == 1


def test_andere_boten_hebben_verwijderen_in_het_blok_boot_wijzigen_of_verwijderen(ingelogd):
    b = boot(lid().id)
    tekst = ingelogd.get(f"/boten/{b.id}").text
    assert '<summary id="wijzigen-kop">Boot wijzigen of verwijderen</summary>' in tekst
    assert "Boot Zeemeeuw verwijderen" not in taak(tekst) and tekst.count("Boot Zeemeeuw verwijderen") == 1


def test_uitklapblokken_van_boot_zijn_dicht_en_het_log_komt_laatst(ingelogd):
    tekst = ingelogd.get(f"/boten/{boot(lid().id).id}").text
    assert re.findall(r"<summary id=\"([a-z-]+)\">", tekst) == ["wijzigen-kop", "foto-kop", "log-kop"]
    assert "<details open" not in tekst and '<details class="dj-disclosure" open' not in tekst
    assert '<summary id="foto-kop">Foto vervangen</summary>' in tekst


def test_boot_geeft_bootnaam_en_eigenaar_geescapet_terug(ingelogd):
    # Mutant: |safe op boot.naam of boot.lid.naam in boot.html valt hier.
    plaats()
    b = boot(lid(naam=XSS).id, naam=XSS, foto=png())
    wachtlijst.erop_zetten(b.id, "2024-03-01", CLI)
    tekst = ingelogd.get(f"/boten/{b.id}").text
    assert XSS not in tekst and GEESCAPET in tekst
    assert f'alt="Foto van {GEESCAPET}"' in tekst  # de alt van de foto
    assert f">{GEESCAPET}</a></dd>" in tekst  # de eigenaarslink
    assert f"Boot {GEESCAPET} verwijderen" in tekst
    oud = lid("1003", "Oud Lid")
    b = boot(oud.id, naam=XSS)
    opzeggen(oud.id, opzegdatum=vandaag())
    tekst = ingelogd.get(f"/boten/{b.id}").text  # de gevaarknop in de taak van een oud-lid
    assert XSS not in tekst and f"Boot {GEESCAPET} verwijderen" in tekst


# Lid


def test_lid_toont_boten_als_lijst_met_wachtlijst_alleen_bij_een_boot_op_de_lijst(ingelogd):
    anna = lid()
    p = plaats()
    met = boot(anna.id, naam="Bezetter")
    toewijzing.toewijzen(p.id, met.id, CLI)
    wacht = boot(anna.id, naam="Wachter")
    wachtlijst.erop_zetten(wacht.id, "2024-03-01", CLI)
    boot(anna.id, naam="Losse")
    tekst = ingelogd.get(f"/leden/{anna.id}").text
    items = {re.search(r'data-label="Boot"[^>]*>([^<]*)<', i).group(1): i for i in re.findall(
        r'<li class="bl-item">(.*?)</li>', tekst.split("Log</summary>")[0], re.DOTALL)}
    assert list(items) == ["Bezetter", "Losse", "Wachter"]  # op naam
    assert f'href="/plaatsen/{p.id}">{p.code}</a>' in items["Bezetter"] and "Wachtlijst" not in items["Bezetter"]
    assert 'Wachtlijst: <span data-label="Wachtlijst">Sinds 01-03-2024</span>' in items["Wachter"]
    assert 'data-label="Plaats">Geen plaats</span>' in items["Losse"] and "Wachtlijst" not in items["Losse"]
    assert "<table" not in tekst


def test_lid_zonder_boten_en_oud_lid(ingelogd):
    anna = lid()
    tekst = ingelogd.get(f"/leden/{anna.id}").text
    assert 'role="status">Dit lid heeft geen boten in de loods.</div>' in tekst
    assert "Lidnummer 1001." in tekst
    oud = oud_lid_boot().lid
    assert "Lidnummer 1003, oud-lid." in ingelogd.get(f"/leden/{oud.id}").text


def test_lid_geeft_naam_en_bootnaam_geescapet_terug(ingelogd):
    # Mutant: |safe op lid.naam of b.naam in lid.html valt hier.
    x = lid(naam=XSS)
    boot(x.id, naam=XSS)
    tekst = ingelogd.get(f"/leden/{x.id}").text
    assert XSS not in tekst and GEESCAPET in tekst
