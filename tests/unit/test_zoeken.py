"""Zoeken vanuit de kop en de resultaatpagina (#154, BV-75): wat een treffer is, de volgorde, de
grenzen (2 tekens, 50 treffers, 100 tekens), het doorsturen bij één treffer, het kopveld en het
escapen van gebruikersinvoer. Elk zoekveld heeft een eigen treffer, zodat een mutant die dat veld uit
de voorwaarde haalt valt."""

import re
from datetime import timedelta

import pytest
from sqlalchemy import select, text

from app.domein import CLI, indeling, toewijzing, vandaag, zoekopdracht
from app.models import Boot, Logregel, Plaats, db
from tests.unit.hulp import beheerder_met_wachtwoord, lid, plaats
from tests.unit.test_blok3a_lijsten import GEESCAPET, XSS, aantal, titels
from tests.unit.test_indeling_en_toewijzing import boot, soort
from tests.unit.test_overzichten_en_instellingen import opzeggen
from tests.unit.test_web import inloggen

NOTITIE = "Typ minstens 2 tekens."
BEGIN = "<b>x"  # het begin van XSS: een rek- of bootsoortnaam mag geen / bevatten
BEGIN_GEESCAPET = "&lt;b&gt;x"


@pytest.fixture
def ingelogd(client):
    _b, geheim = beheerder_met_wachtwoord()
    inloggen(client, geheim)
    return client


def op_plaats(code, b):
    toewijzing.toewijzen(plaats(code).id, b.id, CLI)


@pytest.fixture
def loods(ingelogd):
    """Q/1/1 bezet door Reiger van Anna Zwaan (1001), Q/1/2 vrij, Q/1/3 clubplaats; R/1/1 bezet door
    de clubboot Klipper; Wulp van Bert Fuut (1002) heeft geen plaats; Tureluur heeft geen eigenaar;
    Cor Meeuw (1003) en oud-lid Dirk Oud (2001) hebben geen boot; oud-lid Els Oud (2002) heeft
    Kievit op Q/1/4."""
    anna, bert, _cor, dirk, els = (lid("1001", "Anna Zwaan"), lid("1002", "Bert Fuut"),
                                  lid("1003", "Cor Meeuw"), lid("2001", "Dirk Oud"), lid("2002", "Els Oud"))
    op_plaats("Q/1/1", boot(anna.id, "Kajak", "Reiger"))
    plaats("Q/1/2")
    plaats("Q/1/3", club=True)
    op_plaats("R/1/1", boot(None, "Kajak", "Klipper"))
    boot(bert.id, "Kajak", "Wulp")
    boot(None, "Kajak", "Tureluur", onbekend=True)
    op_plaats("Q/1/4", boot(els.id, "Kajak", "Kievit"))
    gisteren = vandaag() - timedelta(days=1)
    opzeggen(dirk.id, opzegdatum=gisteren)
    opzeggen(els.id, uit_bron_op=gisteren)
    return ingelogd


def kort(term):
    """De treffers als (soort, naam of code), in volgorde."""
    r = zoekopdracht.zoek(term)
    return [(s, o.code if s == "plaats" else o.naam) for s, o in r.treffers]


# Elk zoekveld en elke soort treffer


@pytest.mark.parametrize(("term", "verwacht"), [
    ("reiger", [("boot", "Reiger")]),                       # bootnaam
    ("ZWAAN", [("boot", "Reiger")]),                        # naam van de eigenaar, hoofdletters
    ("1002", [("boot", "Wulp")]),                           # lidnummer van een lid met één boot: de boot
    ("Q/1/1", [("boot", "Reiger")]),                        # plaatscode van een bezette plaats: de boot, geen plaats
    ("R/1", [("boot", "Klipper")]),                         # clubboot
    ("tureluur", [("boot", "Tureluur")]),                   # eigenaar onbekend, geen plaats
    ("wulp", [("boot", "Wulp")]),                           # boot zonder plaats
    ("els", [("boot", "Kievit")]),                          # boot van een oud-lid
    ("meeuw", [("lid", "Cor Meeuw")]),                      # lid zonder boot, naam
    ("1003", [("lid", "Cor Meeuw")]),                       # lid zonder boot, lidnummer
    ("dirk", [("lid", "Dirk Oud")]),                        # oud-lid zonder boot, naam
    ("2001", [("lid", "Dirk Oud")]),                        # oud-lid zonder boot, lidnummer
    ("Q/1/2", [("plaats", "Q/1/2")]),                       # vrije plaats
    ("q/1/3", [("plaats", "Q/1/3")]),                       # vrije clubplaats
], ids=["bootnaam", "eigenaar", "lidnummer-eigenaar", "plaatscode", "clubboot", "onbekende-eigenaar",
        "zonder-plaats", "oud-lid-met-boot", "lid-naam", "lid-lidnummer", "oud-lid-naam",
        "oud-lid-lidnummer", "vrije-plaats", "clubplaats"])
def test_elk_zoekveld_en_elke_soort_treffer_vindt_precies_dit(loods, term, verwacht):
    # Mutant: bevat(Boot.naam), bevat(Lid.naam), bevat(Lid.lidnummer) of bevat(Plaats.code) uit de
    # boten-voorwaarde halen valt op de rij bootnaam, eigenaar, lidnummer-eigenaar of plaatscode; de
    # voorwaarde `~Lid.boten.any()` weglaten geeft ook het lid (eigenaar, lidnummer-eigenaar); de
    # voorwaarde `Plaats.boot_id.is_(None)` weglaten geeft ook de plaats (plaatscode).
    assert kort(term) == verwacht


def test_lid_met_twee_boten_is_alleen_via_zijn_boten_te_vinden(loods):
    boot(lid("1010", "Fien Dubbel").id, "Kajak", "Fuut")
    boot(db.session.scalar(select(Boot.lid_id).where(Boot.naam == "Fuut")), "Surfski", "Aalscholver")
    assert kort("1010") == [("boot", "Aalscholver"), ("boot", "Fuut")]


def test_term_zonder_onderscheid_in_accenten_en_deel_van_de_naam(app):
    boot(lid("1001", "José Zwaan").id, "Kajak", "Café")
    assert kort("JOSE") == [("boot", "Café")] and kort("cafe") == [("boot", "Café")] and kort("fé") == [("boot", "Café")]


def test_procent_en_liggend_streepje_zijn_letterlijk(app):
    boot(None, "Kajak", "Zee_meeuw")
    boot(None, "Kajak", "Zeemeeuw")
    boot(None, "Kajak", "Korting 50%")
    boot(None, "Kajak", "Korting 500")
    assert kort("e_m") == [("boot", "Zee_meeuw")] and kort("50%") == [("boot", "Korting 50%")]
    assert kort("%%") == [] and kort("__") == []


# Volgorde, per sleutel


def test_volgorde_is_eerst_boten_dan_leden_zonder_boot_dan_plaatsen_zonder_boot(app):
    # Mutant: de drie lijsten in een andere volgorde samenvoegen valt hier.
    plaats("Zz/1/1")
    lid("1001", "Zz Lid")
    boot(None, "Kajak", "Zz-boot")
    assert kort("zz") == [("boot", "Zz-boot"), ("lid", "Zz Lid"), ("plaats", "Zz/1/1")]


def test_boten_op_naam_en_bij_gelijke_naam_op_id(app):
    # Mutant: Boot.naam uit de volgorde halen geeft Zeemeeuw (id 1) vóór Aalscholver; Boot.id weglaten
    # geeft bij de twee Reigers de volgorde van de rijen in de tabel, en die is hier omgedraaid.
    boot(None, "Kajak", "Zeemeeuw vogel")
    boot(None, "Kajak", "Aalscholver vogel")
    eerste, tweede = boot(None, "Kajak", "Reiger vogel"), boot(None, "Kajak", "Reiger vogel")
    db.session.execute(text("UPDATE boot SET naam = 'x' WHERE id = :i"), {"i": eerste.id})
    db.session.execute(text("UPDATE boot SET naam = 'Reiger vogel' WHERE id = :i"), {"i": eerste.id})
    db.session.commit()
    treffers = zoekopdracht.zoek("vogel").treffers
    assert [o.naam for _s, o in treffers] == ["Aalscholver vogel", "Reiger vogel", "Reiger vogel", "Zeemeeuw vogel"]
    assert [o.id for _s, o in treffers[1:3]] == [eerste.id, tweede.id]


def test_leden_zonder_boot_op_naam_en_bij_gelijke_naam_op_lidnummer(app):
    # Mutant: Lid.naam weglaten geeft Zeger (id 1) vóór Aad; Lid.lidnummer weglaten geeft 3001 vóór 3000.
    lid("3001", "Zeger Test")
    lid("3000", "Zeger Test")
    lid("3002", "Aad Test")
    assert [(o.naam, o.lidnummer) for _s, o in zoekopdracht.zoek("test").treffers] == [
        ("Aad Test", "3002"), ("Zeger Test", "3000"), ("Zeger Test", "3001")]


def test_plaatsen_op_verdieping_en_vak_niet_op_code(app, database):
    # Mutant: Plaats.verdieping weglaten geeft M/2/1 vóór M/1/2; Plaats.vak weglaten geeft de volgorde
    # van de rijen in de tabel, en die is hier door de UPDATEs omgedraaid; sorteren op code geeft M/1/10 vóór M/1/2.
    indeling.rek_aanmaken("M", "", {(1, v) for v in range(1, 11)} | {(2, 1)}, CLI)
    for vak in range(10, 0, -1):  # elke UPDATE zet de rij achteraan: de rijen staan nu van vak 10 naar 1
        with database.begin() as c:
            c.execute(text("UPDATE plaats SET vak = vak WHERE verdieping = 1 AND vak = :v"), {"v": vak})
    # Zonder statistieken kiest de planner de unieke index en sorteert die al op vak (Sentinel, #154).
    with database.begin() as c:
        c.execute(text("ANALYZE plaats"))
        c.execute(text("ANALYZE rek"))
    codes = [f"M/1/{v}" for v in range(1, 11)] + ["M/2/1"]
    assert kort("m/") == [("plaats", c) for c in codes]


def test_plaatsen_in_de_volgorde_van_de_rekken_in_de_loods(app, database):
    # Mutant: Rek.volgorde weglaten geeft M (id 1) vóór L, dat nu vooraan staat.
    plaats("M/1/1")
    plaats("L/1/1")
    with database.begin() as c:
        c.execute(text("UPDATE rek SET volgorde = CASE naam WHEN 'L' THEN 1 ELSE 2 END"))
    assert kort("/1/1") == [("plaats", "L/1/1"), ("plaats", "M/1/1")]


def test_rekken_met_dezelfde_volgorde_op_rek_id(app, database):
    # Mutant: Rek.id weglaten geeft L/1/1 vóór M/2/1 (dan telt de verdieping), terwijl M het eerste rek is.
    plaats("M/2/1")
    plaats("L/1/1")
    with database.begin() as c:
        c.execute(text("UPDATE rek SET volgorde = 0"))
    assert kort("/1") == [("plaats", "M/2/1"), ("plaats", "L/1/1")]


# De pagina


def pagina(client, term):
    return client.get("/zoeken", query_string={"q": term})


def test_zoeken_vraagt_inloggen_zoals_de_andere_beheerroutes(client):
    r = client.get("/zoeken?q=reiger")
    assert r.status_code == 302 and r.location.endswith("/inloggen")


@pytest.mark.parametrize(("term", "pad"), [
    ("tureluur", "/boten/{}"), ("1003", "/leden/{}"), ("Q/1/2", "/plaatsen/{}"), ("1002", "/boten/{}"),
], ids=["boot", "lid", "plaats", "lid-met-een-boot-geeft-de-boot"])
def test_een_treffer_stuurt_door_naar_boot_lid_of_plaats(loods, term, pad):
    # Mutant: de doorverwijzing weglaten, of de route van een soort verwisselen, valt op de status of de locatie.
    (_soort, o), = zoekopdracht.zoek(term).treffers
    r = pagina(loods, term)
    assert r.status_code == 302 and r.location == pad.format(o.id)


def test_twee_treffers_geven_een_lijst_met_aantal(loods):
    r = pagina(loods, "oud")
    assert r.status_code == 200 and aantal(r.text) == '2 treffers voor "oud"'
    assert titels(r.text) == ["Kievit", "Dirk Oud"]


def rij(html, titel):
    """De li van het item met deze titel."""
    return re.search(rf'<li class="bl-item">(?:(?!</li>).)*>{re.escape(titel)}</a>.*?</li>', html, re.DOTALL).group(0)


def test_lijst_toont_boot_met_eigenaar_en_plaats_en_de_vrije_plaats_of_clubplaats(loods):
    html = pagina(loods, "q/1").text
    assert aantal(html) == '4 treffers voor "q/1"' and titels(html) == ["Kievit", "Reiger", "Q/1/2", "Q/1/3"]
    kievit = rij(html, "Kievit")
    assert 'data-label="Eigenaar">Els Oud (2002)</span> <span class="ds-tag">oud-lid</span>' in kievit
    assert 'data-label="Plaats" href="/plaatsen/' in kievit and ">Q/1/4</a>" in kievit
    reiger = rij(html, "Reiger")
    assert "Anna Zwaan (1001)" in reiger and "oud-lid" not in reiger and 'data-label="Bootsoort">Kajak<' in reiger
    # Mutant: de twee subregels verwisselen valt hier.
    assert '<a class="bl-item__titel" data-label="Plaats" href="/plaatsen/' in rij(html, "Q/1/2")
    assert '<span class="bl-item__sub">vrije plaats</span>' in rij(html, "Q/1/2")
    assert '<span class="bl-item__sub">clubplaats</span>' in rij(html, "Q/1/3")
    assert "bl-item__zijde" not in rij(html, "Q/1/2")


def test_lijst_toont_clubboot_onbekende_eigenaar_boot_zonder_plaats_en_lid_zonder_boot(loods):
    # Elke term krijgt een tweede treffer, zodat de pagina een lijst toont en niet doorstuurt.
    boot(None, "Kajak", "Klipper 2")
    boot(None, "Kajak", "Tureluur 2", onbekend=True)
    boot(None, "Kajak", "Wulp 2", onbekend=True)
    lid("1004", "Cor Meeuw 2")
    klipper = rij(pagina(loods, "klipper").text, "Klipper")
    assert 'data-label="Eigenaar">clubboot<' in klipper and ">R/1/1</a>" in klipper
    tureluur = rij(pagina(loods, "tureluur").text, "Tureluur")
    assert 'data-label="Eigenaar">eigenaar onbekend<' in tureluur and "geen plaats" in tureluur
    assert "geen plaats" in rij(pagina(loods, "wulp").text, "Wulp")
    meeuw = rij(pagina(loods, "cor meeuw").text, "Cor Meeuw")
    assert 'Lidnummer <span data-label="Lidnummer">1003</span>' in meeuw and 'data-label="Boot">geen boot<' in meeuw
    assert "bl-item__zijde" not in meeuw


def test_oud_lid_met_boot_heeft_een_tag_en_een_lid_van_nu_niet(loods):
    # Mutant: de tag altijd of nooit tonen valt op een van beide asserts.
    boot(None, "Kajak", "Zwaan")
    assert 'class="ds-tag">oud-lid</span>' in rij(pagina(loods, "oud").text, "Kievit")
    assert "ds-tag" not in rij(pagina(loods, "zwaan").text, "Reiger")


@pytest.mark.parametrize("term", ["zzz", "  zzz  "], ids=["gewoon", "met-spaties"])
def test_geen_treffers_toont_alleen_de_melding_met_hint_en_geen_aantal(loods, term):
    html = pagina(loods, term).text
    assert 'role="status">Geen treffers voor "zzz".</div>' in html
    assert ("<p>Zoek op een deel van een plaatscode (zoals B/2), een bootnaam, de naam van een eigenaar of "
            "een lidnummer. Oud-leden tellen mee.</p>") in html
    assert "bl-aantal" not in html and "bl-lijst" not in html and NOTITIE not in html


# Grens van 2 tekens


@pytest.mark.parametrize("term", ["", "q", "  q  ", "   ", " u "], ids=["leeg", "een", "een-met-spaties", "spaties", "een-u"])
def test_een_term_onder_twee_tekens_zoekt_niet_en_stuurt_niet_door(loods, term):
    # Mutant: de grens op 1 of op 3 zetten, of niet strippen, valt hier of in de test met twee tekens.
    r = pagina(loods, term)
    assert r.status_code == 200 and f'role="status">{NOTITIE}</div>' in r.text
    assert "bl-lijst" not in r.text and "Geen treffers" not in r.text


def test_zonder_term_in_de_url_is_er_dezelfde_melding(loods):
    r = loods.get("/zoeken")
    assert r.status_code == 200 and NOTITIE in r.text


@pytest.mark.parametrize("term", ["uw", "  uw  "], ids=["twee", "twee-met-spaties"])
def test_een_term_van_twee_tekens_zoekt_wel(loods, term):
    # "uw" staat alleen in Cor Meeuw. Mutant: grens `<=` in plaats van `<` geeft de melding.
    r = pagina(loods, term)
    assert r.status_code == 302 and NOTITIE not in r.text


# Grens van 50 treffers en 100 tekens


def meerkoeten(aantal_boten):
    for i in range(aantal_boten):
        boot(None, "Kajak", f"Meerkoet {i:02d}")


def test_precies_vijftig_treffers_zijn_er_vijftig_zonder_waarschuwing(app, ingelogd):
    # 49 boten en één lid zonder boot. Mutant: MAX_TREFFERS op 49 geeft "Eerste 49 van 50" en 49 items.
    meerkoeten(49)
    lid("4000", "Meerkoet Lid")
    html = pagina(ingelogd, "meerkoet").text
    assert aantal(html) == '50 treffers voor "meerkoet"' and len(titels(html)) == 50 and titels(html)[-1] == "Meerkoet Lid"


def test_eenenvijftig_treffers_toont_de_eerste_vijftig_en_telt_alle(app, ingelogd):
    # Mutant: MAX_TREFFERS op 51 of het afkappen weglaten geeft 51 items; het totaal alleen uit de boten
    # laten komen geeft "van 50".
    meerkoeten(50)
    lid("4000", "Meerkoet Lid")
    html = pagina(ingelogd, "meerkoet").text
    assert aantal(html) == "Eerste 50 van 51 treffers. Zoek preciezer."
    assert titels(html) == [f"Meerkoet {i:02d}" for i in range(50)]


def test_term_wordt_afgekapt_op_honderd_tekens(ingelogd):
    # Mutant: het afkappen weglaten vindt de boot niet meer (200 met melding in plaats van 302).
    boot(None, "Kajak", "a" * 100)
    assert zoekopdracht.schoon("a" * 150) == "a" * 100
    assert pagina(ingelogd, "a" * 150).status_code == 302
    html = pagina(ingelogd, "z" * 150).text
    assert f'Geen treffers voor "{"z" * 100}".' in html and f'value="{"z" * 100}"' in html


def test_term_met_nul_teken_geeft_400_zoals_de_andere_zoekvelden(ingelogd):
    assert ingelogd.get("/zoeken?q=%00").status_code == 400


# Privacy


def test_de_term_komt_niet_in_het_applicatielog_en_niet_in_het_mutatielog(loods, caplog):
    # Mutant: een logregel met de term in de domeinfunctie of de route valt hier.
    voor = db.session.scalar(select(db.func.count()).select_from(Logregel))
    with caplog.at_level("DEBUG"):
        pagina(loods, "geheimeterm")
        pagina(loods, "reiger")
        pagina(loods, "x")
    assert "geheimeterm" not in caplog.text and "reiger" not in caplog.text.lower()
    assert db.session.scalar(select(db.func.count()).select_from(Logregel)) == voor


# Het kopveld


def test_kopveld_staat_op_elke_beheerpagina_met_label_knop_en_unieke_id(loods):
    # Mutant: id terugzetten op "zoek" geeft op Leden een dubbele id; het veld buiten `g.beheerder` valt
    # in de test voor de bezoeker.
    for pad in ("/rekoverzicht", "/leden", "/boten", "/zoeken?q=reiger"):
        html = loods.get(pad, follow_redirects=True).text
        kop = html.split("</header>")[0]
        assert kop.count('role="search"') == 1 and html.count('id="kop-zoek"') == 1 and html.count('id="zoek"') <= 1
        assert '<label class="dj-sr-only" for="kop-zoek">Zoeken naar plaats, boot of eigenaar</label>' in kop
        assert 'type="search" id="kop-zoek" name="q"' in kop and 'maxlength="100"' in kop
        assert 'placeholder="Plaats, boot of eigenaar"' in kop and 'action="/zoeken"' in kop and 'method="get"' in kop
        assert '<button type="submit" class="ds-btn ds-btn--primary">Zoeken</button>' in kop
        # Tussen het logo en het menu.
        assert kop.index("dj-logo") < kop.index("dj-search") < kop.index("dj-menu")
    assert 'id="zoek"' in loods.get("/leden").text


def test_kopveld_toont_de_term_op_de_resultaatpagina_en_anders_niets(loods):
    assert 'id="kop-zoek" name="q" value="oud"' in pagina(loods, "  oud ").text
    assert 'id="kop-zoek" name="q" value=""' in loods.get("/rekoverzicht").text


def test_kopveld_ontbreekt_voor_een_bezoeker_en_op_de_openbare_pagina(loods, client, app):
    # Mutant: het veld buiten `g.beheerder` zetten valt op de eerste assert; de overschrijving van
    # `block menu` in openbaar.html weghalen valt op de tweede (een ingelogde beheerder op de openbare pagina).
    bezoeker = app.test_client()
    assert "kop-zoek" not in bezoeker.get("/inloggen").text
    sleutel = db.session.scalar(select(Plaats.publieke_sleutel).limit(1))
    for c in (bezoeker, loods):
        r = c.get(f"/p/{sleutel}")
        assert r.status_code == 200 and "kop-zoek" not in r.text and "<input" not in r.text


# Gebruikersinvoer wordt geëscapet


def test_term_in_melding_aantal_en_kopveld_is_geescaped(loods):
    # Mutant: |safe op zoekterm in de melding, het aantal of het kopveld (base.html) valt hier.
    boot(None, "Kajak", f"{XSS} een")
    boot(None, "Kajak", f"{XSS} twee")
    geen = pagina(loods, f"{XSS}{XSS}").text
    assert XSS not in geen and geen.count(GEESCAPET) == 4 and f'Geen treffers voor "{GEESCAPET}{GEESCAPET}".' in geen
    veel = pagina(loods, XSS).text
    assert XSS not in veel and f'2 treffers voor "{GEESCAPET}"' in veel and f'value="{GEESCAPET}"' in veel


def test_boot_eigenaar_lidnummer_bootsoort_en_plaatscode_zijn_geescaped(loods):
    # Mutant: |safe op de bootnaam, de naam van de eigenaar, het lidnummer van de eigenaar, de bootsoort of
    # de plaatscode in de bootrij, of op de naam, het lidnummer of de code in de lid- en plaatsrij.
    # Term BEGIN, want een rek- of bootsoortnaam mag geen / bevatten.
    indeling.bootsoort_hernoemen(soort("C11"), BEGIN, CLI)
    c11 = soort(BEGIN)
    b = boot(None, BEGIN, f"{BEGIN} met soort en plaats")
    toewijzing.toewijzen(plaats(f"{BEGIN}/1/1", (c11,)).id, b.id, CLI)
    boot_id = b.id
    boot(lid("N1", f"{BEGIN} eigenaar").id, "Kajak", "Eigenaar")
    boot(lid(f"{BEGIN}1", "Lidnummer").id, "Kajak", "Lidnr")
    lid("N2", f"{BEGIN} zonder boot")
    lid(f"{BEGIN}2", "Lidnummer zonder boot")
    plaats(f"{BEGIN}/1/2")
    html = pagina(loods, BEGIN).text
    assert "<b>" not in html
    G = BEGIN_GEESCAPET
    for veld in (f'data-label="Boot" href="/boten/{boot_id}">{G} met soort en plaats</a>', f'data-label="Bootsoort">{G}<',
                 f'data-label="Eigenaar">{G} eigenaar (N1)', f'data-label="Eigenaar">Lidnummer ({G}1)',
                 'data-label="Plaats" href="/plaatsen/', f'>{G}/1/1</a>', f'>{G}/1/2</a>',
                 'data-label="Lid" href="/leden/', f'>{G} zonder boot</a>', f'data-label="Lidnummer">{G}2</span>'):
        assert veld in html, veld
