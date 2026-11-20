"""Kijkers (BLB-050, BLB-051, ADR-015, issue #322): de centrale rolcontrole, wat een kijker ziet en wat de
server weigert. Elke route buiten KIJKER_TOEGESTAAN geeft een kijker 403 voor elke methode; elk scherm
dat hij wel ziet, toont geen knoppen, leden of lidnummers."""

import re
from datetime import timedelta

import pytest
from flask import g
from sqlalchemy import text
from werkzeug.routing import AnyConverter, IntegerConverter

from app.domein import CLI, Actor, beheerders, boten, indeling, log, toewijzing, vandaag, wachtlijst
from app.models import Beheerder, db
from app.web import KIJKER_TOEGESTAAN
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.test_indeling_en_toewijzing import boot
from tests.unit.test_overzichten_en_instellingen import opzeggen
from tests.unit.test_web import inloggen

LIDNUMMER = "7654321"


def main(tekst):
    return re.search(r"<main.*?</main>", tekst, re.DOTALL).group(0)


def als_kijker(app):
    """(client, kijker) ingelogd als kijker `kees`."""
    kijker, geheim = beheerder_met_wachtwoord("kees", "kijker")
    client = app.test_client()
    inloggen(client, geheim, gebruikersnaam="kees")
    return client, kijker


@pytest.fixture
def kijker(app):
    return als_kijker(app)[0]


@pytest.fixture
def beheerder(app):
    _, geheim = beheerder_met_wachtwoord("anna")
    client = app.test_client()
    inloggen(client, geheim)
    return client


@pytest.fixture
def loods(app):
    """Plaats A/1/1 bezet door Zeemeeuw van Anna de Vries (LIDNUMMER), A/1/2 vrij, Wulp van Bert zonder
    plaats op de wachtlijst, en een lid Cor zonder boot. Geeft de boot en de bezette plaats."""
    anna, bert = lid(LIDNUMMER, "Anna de Vries"), lid("1002", "Bert Fuut")
    lid("1003", "Cor Meeuw")
    zee = boot(anna.id, "Kajak", "Zeemeeuw")
    p = plaats("A/1/1")
    plaats("A/1/2")
    toewijzing.toewijzen(p.id, zee.id, CLI)
    wulp = boot(bert.id, "Kajak", "Wulp")
    wachtlijst.erop_zetten(wulp.id, None, CLI)
    return zee, p, wulp


# De centrale controle (ADR-015)


def web_routes(app):
    return [r for r in app.url_map.iter_rules() if r.endpoint.startswith("web.")]


def voorbeeld_url(regel):
    """Een url voor de regel: 1 voor een getal, de eerste keuze van een any(), anders x."""
    waarden = {naam: 1 if isinstance(conv, IntegerConverter) else min(conv.items) if isinstance(conv, AnyConverter) else "x"
               for naam, conv in regel._converters.items()}
    return regel.build(waarden)[1]


def test_elke_route_buiten_de_lijst_geeft_een_kijker_403_voor_elke_methode(app):
    client, _ = als_kijker(app)
    gedaan = []
    for regel in web_routes(app):
        if regel.endpoint in KIJKER_TOEGESTAAN or regel.endpoint == "web.beheerders_oud":
            continue
        url = voorbeeld_url(regel)
        for methode in sorted(regel.methods - {"HEAD", "OPTIONS"}):
            r = client.open(url, method=methode)
            assert r.status_code == 403, (methode, url, r.status_code)
            gedaan.append((methode, url))
    # Er zijn veel POST-routes; een walk die niets doet, bewijst niets.
    assert sum(m == "POST" for m, _ in gedaan) >= 30 and sum(m == "GET" for m, _ in gedaan) >= 20, gedaan


def test_de_oude_beheerders_url_geeft_een_kijker_403(app):
    client, _ = als_kijker(app)
    assert client.get("/beheerders").status_code == 403


def test_elk_endpoint_in_de_lijst_bestaat(app):
    assert KIJKER_TOEGESTAAN <= {r.endpoint for r in web_routes(app)}


def test_de_lijst_heeft_de_tien_inzien_endpoints_en_de_vijftien_van_inloggen(app):
    inloggen_py = {r.endpoint for r in web_routes(app) if app.view_functions[r.endpoint].__module__ == "app.web.inloggen"}
    assert len(inloggen_py) == 15 and inloggen_py <= KIJKER_TOEGESTAAN
    assert len(KIJKER_TOEGESTAAN) == 25
    # Een route die de lijst niet noemt, is dicht; de lijst wijzigt alleen met een besluit.
    for dicht in ("web.wachtlijst_overzicht", "web.leden_overzicht", "web.lid_detail", "web.logboek", "web.technisch_log",
                  "web.tokens_overzicht", "web.statuspagina", "web.instellingen_scherm", "web.beheerders_overzicht",
                  "web.indeling_overzicht", "web.opgezegd", "web.opzeggend", "web.kaartjes_kiezen"):
        assert dicht not in KIJKER_TOEGESTAAN


@pytest.mark.parametrize("pad", ["/", "/rekoverzicht", "/vrij", "/boten", "/zoeken?q=ab", "/profiel", "/inloggen"])
def test_een_kijker_opent_de_toegestane_pagina(kijker, pad):
    assert kijker.get(pad).status_code in (200, 302)


def test_een_kijker_opent_boot_en_plaats(kijker, loods):
    zee, p, _ = loods
    assert kijker.get(f"/boten/{zee.id}").status_code == 200
    assert kijker.get(f"/plaatsen/{p.id}").status_code == 200
    assert kijker.get(f"/p/{p.publieke_sleutel}").status_code == 200


@pytest.mark.parametrize("pad", ["/wachtlijst", "/leden", "/leden/1", "/log", "/log/techniek", "/indeling", "/tokens",
                                 "/tokens/nieuw", "/status", "/status.json", "/instellingen", "/gebruikers",
                                 "/opgezegd", "/opzeggend", "/boten/zonder-eigenaar", "/boten-zonder-foto",
                                 "/kaartjes", "/import-export", "/indeling.xlsx", "/bezetting.csv"])
def test_een_kijker_krijgt_op_een_beheerpagina_403(kijker, pad):
    assert kijker.get(pad).status_code == 403


def test_de_rol_komt_uit_de_database_bij_elk_verzoek_zonder_dat_de_sessie_eindigt(app, beheerder, kijker):
    """Een rolwijziging geldt bij het volgende verzoek (ADR-015): ook de lopende sessie weigert."""
    assert beheerder.get("/gebruikers").status_code == 200
    anna = db.session.scalar(db.select(Beheerder).where(Beheerder.gebruikersnaam == "anna"))
    # Anna is hier de enige beheerder; een tweede beheerder maakt de wijziging mogelijk.
    bert, _ = beheerder_met_wachtwoord("bert")
    beheerders.rol_wijzigen(anna.id, "kijker", Actor.van(bert))
    assert beheerder.get("/gebruikers").status_code == 403
    assert beheerder.get("/rekoverzicht").status_code == 200  # de sessie bleef bestaan
    beheerders.rol_wijzigen(anna.id, "beheerder", Actor.van(bert))
    assert beheerder.get("/gebruikers").status_code == 200


def test_een_onbekende_rol_valt_onder_de_weigering(app, database):
    """Alleen de eigenaar kan de check rol_geldig tijdelijk weghalen; de test zet hem daarna terug."""
    _, geheim = beheerder_met_wachtwoord("kees", "kijker")
    client = app.test_client()
    inloggen(client, geheim, gebruikersnaam="kees")
    db.session.remove()  # geen open transactie die de ALTER TABLE laat wachten
    with database.begin() as c:
        c.execute(text("SET LOCAL lock_timeout = '3s'"))
        c.execute(text("ALTER TABLE beheerder DROP CONSTRAINT rol_geldig"))
        c.execute(text("UPDATE beheerder SET rol = 'x' WHERE gebruikersnaam = 'kees'"))
    try:
        assert client.get("/boten").status_code == 200  # in de lijst
        assert client.get("/leden").status_code == 403
    finally:
        db.session.remove()
        with database.begin() as c:
            c.execute(text("SET LOCAL lock_timeout = '3s'"))
            c.execute(text("DELETE FROM beheerder WHERE rol = 'x'"))
            c.execute(text("ALTER TABLE beheerder ADD CONSTRAINT rol_geldig CHECK (rol IN ('beheerder', 'kijker'))"))


def test_een_kijker_mag_inloggen_uitloggen_en_zijn_eigen_profiel_beheren(app):
    """Besluit 8: de POST-routes van inloggen.py werken voor een kijker, niet met 403."""
    _, geheim = beheerder_met_wachtwoord("kees", "kijker")
    client = app.test_client()
    r = inloggen(client, geheim, gebruikersnaam="kees")
    assert r.status_code == 302 and r.location == "/rekoverzicht"
    # Profiel: intrekken van de enige methode wordt door het domein geweigerd, niet door de rolcontrole.
    r = client.post("/profiel/intrekken", data={"methode": "wachtwoord"})
    assert r.status_code == 302 and r.location.endswith("/profiel")
    assert client.post("/profiel/wachtwoord").status_code == 302
    assert client.post("/profiel/passkey/opties").status_code == 200
    assert client.post("/uitloggen").status_code == 302
    assert client.get("/rekoverzicht").location.startswith("/inloggen")


# Wat een kijker ziet


def test_het_menu_van_een_kijker_is_een_lijst_zonder_groepskoppen_met_vijf_items(kijker):
    tekst = kijker.get("/rekoverzicht").text
    menu = re.search(r'<nav class="dj-menu__panel".*?</nav>', tekst, re.DOTALL).group(0)
    assert re.findall(r">([^<>]+)</(?:a|button)>", menu) == ["Rekoverzicht", "Vrije plaatsen", "Boten", "Profiel", "Uitloggen"]
    assert "bl-nav__groep" not in menu and "aria-labelledby" not in menu and "bl-nav__aantal" not in menu
    assert "Overal zoeken" in tekst  # het zoekveld in de kop blijft


def test_het_menu_van_een_kijker_toont_het_aantal_boten_zonder_eigenaar_niet(kijker):
    boot(None, "Kajak", "Tureluur", onbekend=True)
    tekst = kijker.get("/rekoverzicht").text
    assert "Boten zonder eigenaar" not in tekst and "bl-nav__aantal" not in tekst


def test_het_menu_van_een_beheerder_heet_gebruikers_en_telt_wel(beheerder):
    boot(None, "Kajak", "Tureluur", onbekend=True)
    tekst = beheerder.get("/rekoverzicht").text
    assert 'href="/gebruikers">Gebruikers</a>' in tekst and "Beheerders</a>" not in tekst
    assert "bl-nav__aantal" in tekst


def test_boten_voor_een_kijker_heeft_geen_nieuwe_boot_en_een_eigenaar_zonder_link(kijker, loods):
    tekst = main(kijker.get("/boten").text)
    assert "Nieuwe boot" not in tekst and "<form" in tekst and tekst.count("<form") == 1  # alleen het filter
    assert 'method="post"' not in tekst and "Zoek op boot of eigenaar" in tekst
    assert "Anna de Vries" in tekst and "/leden/" not in tekst and LIDNUMMER not in tekst


def test_het_filter_op_boten_zoekt_voor_een_kijker_niet_op_lidnummer(kijker, loods):
    def lijst(zoek):  # het log onder de lijst noemt de boot ook
        return re.search(r'<ul class="bl-lijst">.*?</ul>|<div class="ds-notice.*?</div>', kijker.get(f"/boten?zoek={zoek}").text, re.DOTALL).group(0)

    assert "Zeemeeuw" not in lijst(LIDNUMMER) and "Geen boten gevonden" in lijst(LIDNUMMER)
    assert "Zeemeeuw" in lijst("Anna")


def test_een_boot_met_plaats_voor_een_kijker_toont_alleen_de_feiten_en_het_log(kijker, loods):
    zee, p, _ = loods
    tekst = main(kijker.get(f"/boten/{zee.id}").text)
    assert "<form" not in tekst and "<button" not in tekst and "<input" not in tekst
    for weg in ("Vrijgeven doe je op de plaats", "Boot verplaatsen", "Boot wijzigen", "Foto vervangen", "bl-taak", "Op plaats"):
        assert weg not in tekst, weg
    assert re.search(r"<dt>Eigenaar</dt>\s*<dd>Anna de Vries</dd>", tekst) and "/leden/" not in tekst
    assert f'href="/plaatsen/{p.id}"' in tekst and 'id="log-kop"' in tekst


def test_een_boot_zonder_plaats_voor_een_kijker_toont_geen_regel_wachtlijst(kijker, loods):
    _, _, wulp = loods
    tekst = main(kijker.get(f"/boten/{wulp.id}").text)
    assert "Wachtlijst" not in tekst and "Plaats toewijzen" not in tekst and "<form" not in tekst
    assert "<dt>Plaats</dt> <dd>geen</dd>" in tekst


def test_dezelfde_boot_zonder_plaats_toont_een_beheerder_de_regel_wachtlijst(beheerder, loods):
    _, _, wulp = loods
    assert "<dt>Wachtlijst</dt>" in main(beheerder.get(f"/boten/{wulp.id}").text)


def test_een_boot_van_een_oud_lid_toont_een_kijker_geen_taak_of_oud_lid(kijker, loods):
    oud = lid("2001", "Dirk Oud")
    b = boot(oud.id, "Kajak", "Oudje")
    opzeggen(oud.id, opzegdatum=vandaag() - timedelta(days=1))
    tekst = main(kijker.get(f"/boten/{b.id}").text)
    assert "oud-lid" not in tekst and "Boot verwijderen" not in tekst and "<form" not in tekst


def test_een_bezette_plaats_voor_een_kijker_heeft_panelen_boot_eigenaar_en_openbare_pagina(kijker, loods):
    _, p, _ = loods
    tekst = main(kijker.get(f"/plaatsen/{p.id}").text)
    assert re.findall(r'<h2 class="dj-panel__title"[^>]*>([^<]*)</h2>', tekst) == ["Boot", "Eigenaar", "Openbare pagina"]
    assert "<form" not in tekst and "<button" not in tekst
    assert 'data-veld="naam">Anna de Vries</dd>' in tekst and "/leden/" not in tekst
    assert LIDNUMMER not in tekst and 'data-veld="lidnummer"' not in tekst and "oud-lid" not in tekst


def test_een_plaats_van_een_oud_lid_toont_een_kijker_geen_tag(kijker, loods):
    oud = lid("2001", "Dirk Oud")
    p = plaats("B/1/1")
    toewijzing.toewijzen(p.id, boot(oud.id, "Kajak", "Oudje").id, CLI)
    opzeggen(oud.id, opzegdatum=vandaag() - timedelta(days=1))
    assert "oud-lid" not in kijker.get(f"/plaatsen/{p.id}").text
    assert "oud-lid" in main(db_beheerder_get(kijker.application, p.id))  # de beheerder ziet de tag wel


def db_beheerder_get(app, plaats_id):
    _, geheim = beheerder_met_wachtwoord("anna")
    client = app.test_client()
    inloggen(client, geheim)
    return client.get(f"/plaatsen/{plaats_id}").text


def test_een_vrije_plaats_voor_een_kijker_heeft_geen_lijst_en_geen_knop(kijker, loods):
    vrij = next(p for p in indeling.vrije_plaatsen(None) if p.code == "A/1/2")
    tekst = main(kijker.get(f"/plaatsen/{vrij.id}").text)
    assert "Deze plaats is vrij" in tekst and "<form" not in tekst and "<select" not in tekst
    assert "Plaats toewijzen" not in tekst and "Plaats wijzigen" not in tekst and "Openbare pagina" in tekst


def test_dezelfde_vrije_plaats_toont_een_beheerder_wel_de_formulieren(beheerder, loods):
    vrij = next(p for p in indeling.vrije_plaatsen(None) if p.code == "A/1/2")
    tekst = main(beheerder.get(f"/plaatsen/{vrij.id}").text)
    assert "Plaats toewijzen" in tekst and "Plaats wijzigen" in tekst


def test_rekoverzicht_en_vrije_plaatsen_voor_een_kijker_hebben_geen_formulier_behalve_het_filter(kijker, loods):
    assert "<form" not in main(kijker.get("/rekoverzicht").text)
    vrij = main(kijker.get("/vrij").text)
    assert vrij.count("<form") == 1 and 'method="get"' in vrij and 'method="post"' not in vrij


def test_profiel_voor_een_kijker_toont_zijn_eigen_inlogmethodes(kijker):
    tekst = main(kijker.get("/profiel").text)
    assert "Je inlogmethodes" in tekst and "/profiel/intrekken" in tekst


# Zoeken en log


def test_zoeken_geeft_een_kijker_geen_leden_en_geen_treffer_op_een_lidnummer(kijker, loods):
    assert "Geen treffers" in kijker.get(f"/zoeken?q={LIDNUMMER}").text
    r = kijker.get("/zoeken?q=Cor M")  # Cor heeft geen boot: voor een beheerder een lid als treffer
    tekst = main(r.text)
    assert r.status_code == 200 and "Geen treffers" in tekst and "/leden/" not in tekst
    assert "lidnummer" not in tekst.lower() and "of de naam van een eigenaar." in tekst


def test_zoeken_op_de_naam_van_een_eigenaar_geeft_zijn_boot_zonder_nummer_en_tag(kijker, loods):
    oud = lid("2001", "Dirk Oud")
    boot(oud.id, "Kajak", "Oudje")
    boot(oud.id, "Kajak", "Oudje 2")  # één treffer stuurt door naar de boot
    opzeggen(oud.id, opzegdatum=vandaag() - timedelta(days=1))
    tekst = main(kijker.get("/zoeken?q=Dirk").text)
    assert "Dirk Oud" in tekst and "2001" not in tekst and "oud-lid" not in tekst and "/leden/" not in tekst


def test_een_zoekterm_met_een_lid_zonder_boot_stuurt_een_kijker_niet_naar_een_lid(kijker, loods):
    r = kijker.get("/zoeken?q=Cor Meeuw")
    assert r.status_code == 200  # geen redirect naar /leden/<id>


def test_dezelfde_zoekterm_geeft_een_beheerder_wel_het_lid(beheerder, loods):
    r = beheerder.get("/zoeken?q=Cor Meeuw")
    assert r.status_code == 302 and "/leden/" in r.location


def test_het_log_toont_een_kijker_een_lid_zonder_nummer(kijker, loods):
    zee, p, _ = loods
    boten.boot_wijzigen(zee.id, "Zeemeeuw", zee.bootsoort_id, lid("1004", "Dora Wiel").id, CLI)
    tekst = main(kijker.get(f"/boten/{zee.id}").text)
    assert "Lid Dora Wiel" in tekst and "Lid Anna de Vries" in tekst
    for pad in (f"/boten/{zee.id}", f"/plaatsen/{p.id}", "/boten", "/vrij"):
        tekst = main(kijker.get(pad).text)
        assert "1004" not in tekst and LIDNUMMER not in tekst, pad


def test_het_log_toont_een_beheerder_het_lidnummer_wel(beheerder, loods):
    zee, _, _ = loods
    boten.boot_wijzigen(zee.id, "Zeemeeuw", zee.bootsoort_id, lid("1004", "Dora Wiel").id, CLI)
    assert f"Lid Anna de Vries ({LIDNUMMER})" in beheerder.get(f"/boten/{zee.id}").text


def test_wachtlijstregels_staan_voor_een_kijker_niet_in_het_log_onder_een_boot(kijker, loods):
    _, _, wulp = loods  # staat op de wachtlijst: wachtlijst.toegevoegd
    oud = lid("2001", "Dirk Oud")
    opzeggen(oud.id, opzegdatum=vandaag() - timedelta(days=1))
    boten.boot_wijzigen(wulp.id, "Wulp", wulp.bootsoort_id, oud.id, CLI)  # wachtlijst.verwijderd, reden oud-lid
    tekst = main(kijker.get(f"/boten/{wulp.id}").text)
    assert "boot gewijzigd" in tekst and "wachtlijst" not in tekst and "oud-lid" not in tekst


def test_wachtlijstregels_staan_voor_een_beheerder_wel_in_het_log(beheerder, loods):
    _, _, wulp = loods
    tekst = main(beheerder.get(f"/boten/{wulp.id}").text)
    assert "wachtlijst toegevoegd" in tekst


def test_het_filterlabel_op_boten_noemt_voor_een_kijker_de_eigenaar_en_voor_een_beheerder_het_lid(kijker, beheerder):
    assert "Zoek op boot of eigenaar" in kijker.get("/boten").text and "boot of lid" not in kijker.get("/boten").text
    assert "Zoek op boot of lid" in beheerder.get("/boten").text


def test_meer_in_het_log_vervalt_voor_een_kijker_en_blijft_voor_een_beheerder(app, loods):
    zee, _, _ = loods
    for i in range(55):  # een scherm toont hooguit 50 regels; bij 50 komt de link
        log.schrijf(CLI, "boot.gewijzigd", [f"boot:{zee.id}"], {"naam": [str(i), str(i + 1)]})
    db.session.commit()
    kijker_client, _ = als_kijker(app)
    assert "Meer in het log" not in kijker_client.get(f"/boten/{zee.id}").text
    _, geheim = beheerder_met_wachtwoord("anna")
    client = app.test_client()
    inloggen(client, geheim)
    assert "Meer in het log" in client.get(f"/boten/{zee.id}").text


# Eigen account en gebruikers


def test_gebruikers_heeft_een_rolkeuze_zonder_voorkeur_en_een_knop_per_rij(beheerder):
    bert, _ = beheerder_met_wachtwoord("bert", "kijker")
    tekst = main(beheerder.get("/gebruikers").text)
    assert tekst.count('type="radio" id="rol-') == 2 and "checked" not in tekst
    assert tekst.count('name="rol" value="beheerder" required') == 1 and tekst.count('name="rol" value="kijker" required') == 1
    assert 'aria-label="Maak kijker: anna"' in tekst and 'aria-label="Maak beheerder: bert"' in tekst
    assert f'action="/gebruikers/{bert.id}/rol"' in tekst and "Rol</th>" in tekst
    assert "persoonlijke tokens vervallen" not in tekst and "vervallen zijn persoonlijke tokens" in tekst


def test_de_oude_url_beheerders_verwijst_met_301_naar_gebruikers(client):
    r = client.get("/beheerders")
    assert r.status_code == 301 and r.location.endswith("/gebruikers")


def test_de_oude_post_routes_onder_beheerders_bestaan_niet_meer(beheerder):
    assert beheerder.post("/beheerders", data={"gebruikersnaam": "carla", "rol": "kijker"}).status_code == 405
    assert beheerder.post("/beheerders/1/blokkeren").status_code == 404


def test_is_kijker_is_onwaar_zonder_ingelogd_account_en_voor_een_beheerder_en_waar_voor_een_kijker(app):
    from app.web import is_kijker
    with app.test_request_context("/"):
        g.beheerder = None
        assert is_kijker() is False
        g.beheerder = Beheerder(rol="beheerder")
        assert is_kijker() is False
        g.beheerder = Beheerder(rol="kijker")
        assert is_kijker() is True


def test_de_oude_rolwaarde_beheerder_voor_jezelf_stuurt_niet_naar_rekoverzicht(beheerder):
    anna = db.session.scalar(db.select(Beheerder).where(Beheerder.gebruikersnaam == "anna"))
    r = beheerder.post(f"/gebruikers/{anna.id}/rol", data={"rol": "beheerder"})
    assert r.status_code == 302 and r.location == "/gebruikers"
