"""Eigenaar onbekend (issues #204 en #207): de toestand naast lid en clubboot, de plaatsregels, de
wachtlijst, de pagina Boten zonder eigenaar, het menu, het formulier Nieuwe boot en de API. De CSV
staat in test_bezetting_csv.py, de migratie in test_migratie_en_taken.py."""

import re

import pytest
from sqlalchemy import select

from app.domein import CLI, Regelfout, boten, toewijzing, uitlezen, vandaag, wachtlijst
from app.models import Boot, Logregel, db
from tests.unit.hulp import lid, race
from tests.unit.test_boot_wijzigen import regels, wijzig
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture


def onbekend(naam="Wulp"):
    return boot(None, "Kajak", naam, onbekend=True)


# Domein


def test_aanmaken_zonder_lid_en_zonder_clubboot_is_eigenaar_onbekend(app):
    # Mutant: clubboot=True als standaard (de oude regel "geen lid is clubboot") valt hier.
    b = boten.boot_aanmaken("Wulp", 1, None, None, CLI)
    assert (b.lid_id, b.clubboot) == (None, False)
    gegevens = db.session.scalar(select(Logregel).where(Logregel.actie == "boot.aangemaakt")).gegevens
    assert (gegevens["clubboot"], gegevens["eigenaar_onbekend"]) == (False, True)


def test_een_clubboot_heeft_geen_lid(app):
    with pytest.raises(Regelfout, match="geen lid"):
        boten.boot_aanmaken("Fuut", 1, lid().id, None, CLI, clubboot=True)
    assert db.session.scalar(select(Boot)) is None


def test_onbekende_eigenaar_past_op_een_gewone_plaats_en_clubplaats_weigert_hem(app):
    # Mutant: controleer_past die een onbekende eigenaar als clubboot leest valt op beide helften.
    gewoon, club = plaats("A/1/1"), plaats("A/1/2", club=True)
    b = onbekend()
    assert toewijzing.past(gewoon, b) and not toewijzing.past(club, b)
    with pytest.raises(Regelfout, match="clubplaats en alleen voor clubboten"):
        toewijzing.toewijzen(club.id, b.id, CLI)
    toewijzing.toewijzen(gewoon.id, b.id, CLI)
    assert b.plaats.code == "A/1/1"


def test_onbekende_eigenaar_mag_op_de_wachtlijst_en_een_clubboot_niet(app):
    wachtlijst.erop_zetten(onbekend().id, None, CLI)
    [(_, [w])] = wachtlijst.lijsten()
    assert w.boot.naam == "Wulp" and w.boot.lid is None
    with pytest.raises(Regelfout, match="clubboot kan niet op de wachtlijst"):
        wachtlijst.erop_zetten(boot(None, "Kajak", "Club").id, None, CLI)
    wachtlijst.oud_leden_eraf(CLI, vandaag())
    assert wachtlijst.lijsten()  # een boot zonder lid blijft staan


def test_een_onbekende_boot_wordt_clubboot_of_lid(app):
    anna = lid()
    o = onbekend()
    wijzig(o, lid_id=anna.id)
    assert (o.lid_id, o.clubboot) == (anna.id, False)
    gegevens = db.session.scalars(select(Logregel).where(Logregel.actie == "boot.gewijzigd")).all()[-1].gegevens
    assert gegevens["eigenaar"] == ["onbekend", f"lid:{anna.id}"]


def test_een_boot_van_een_lid_wordt_weer_onbekend_en_houdt_zijn_gewone_plaats(app):
    # #233; mutant: de weigering "wordt niet weer onbekend" terug valt hier.
    anna = lid()
    b = boot(anna.id, "Kajak", "Fuut")
    toewijzing.toewijzen(plaats("A/1/1").id, b.id, CLI)
    wijzig(b, lid_id=None, club=False)
    assert (b.lid_id, b.clubboot, b.plaats.code) == (None, False, "A/1/1")
    assert boten.zonder_eigenaar() == [b]
    gegevens = db.session.scalars(select(Logregel).where(Logregel.actie == "boot.gewijzigd")).all()[-1].gegevens
    assert gegevens["eigenaar"] == [f"lid:{anna.id}", "onbekend"]


def test_een_clubboot_zonder_plaats_wordt_onbekend(app):
    # Mutant: de weigering voor een boot met een eigenaar (oude_club) terug valt hier.
    c = boot(None, "Kajak", "Club")
    wijzig(c, lid_id=None, club=False)
    assert (c.lid_id, c.clubboot) == (None, False)
    gegevens = db.session.scalars(select(Logregel).where(Logregel.actie == "boot.gewijzigd")).all()[-1].gegevens
    assert gegevens["eigenaar"] == ["vereniging", "onbekend"]


def test_een_clubboot_op_een_clubplaats_wordt_niet_onbekend_zolang_hij_daar_ligt(app):
    # Besluit 2026-11-11 (#233). Mutant: `clubboot != oude_club` uit de voorwaarde van
    # controleer_past in boot_wijzigen halen valt op de eerste assert.
    club = plaats("A/1/1", club=True)
    c = boot(None, "Kajak", "Club")
    toewijzing.toewijzen(club.id, c.id, CLI)
    n = len(regels())
    with pytest.raises(Regelfout, match="Plaats A/1/1 is een clubplaats en alleen voor clubboten"):
        wijzig(c, lid_id=None, club=False)
    assert (c.clubboot, c.plaats.code, len(regels())) == (True, "A/1/1", n)
    toewijzing.vrijgeven(club.id, CLI)
    wijzig(c, lid_id=None, club=False)
    assert (c.clubboot, c.plaats) == (False, None)


def test_een_clubboot_op_een_gewone_plaats_wordt_onbekend_en_blijft_liggen(app):
    c = boot(None, "Kajak", "Club")
    toewijzing.toewijzen(plaats("A/1/1").id, c.id, CLI)
    wijzig(c, lid_id=None, club=False)
    assert (c.clubboot, c.plaats.code) == (False, "A/1/1")


def test_een_boot_van_een_lid_op_de_wachtlijst_gaat_eraf_als_hij_onbekend_wordt(app):
    # #233: een andere eigenaar (hier: geen) haalt de boot van de lijst. Mutant: de aanroep
    # wachtlijst._eraf in boot_wijzigen weglaten valt op de eerste assert.
    b = boot(lid().id, "Kajak", "Fuut")
    wachtlijst.erop_zetten(b.id, None, CLI)
    wijzig(b, lid_id=None, club=False)
    assert b.wachtlijst is None and (b.lid_id, b.clubboot) == (None, False)
    assert "wachtlijst.verwijderd" in acties()
    gegevens = db.session.scalars(select(Logregel).where(Logregel.actie == "wachtlijst.verwijderd")).all()[-1].gegevens
    assert gegevens["reden"] == "andere eigenaar"


def test_wijzigen_naar_onbekend_zonder_verschil_schrijft_geen_logregel(app):
    o = onbekend()
    wijzig(o, lid_id=None, club=False)
    assert not regels()


def test_onbekend_naar_clubboot_mag_op_een_gewone_plaats_en_zonder_plaats(app):
    toewijzing.toewijzen(plaats("A/1/1").id, (o := onbekend()).id, CLI)
    wijzig(o, lid_id=None, club=True)  # #205; mutant: de oude regel terug valt hier
    assert o.clubboot is True and o.plaats.code == "A/1/1"
    wijzig(p := onbekend("Zonder"), lid_id=None, club=True)
    assert p.clubboot is True


def test_boot_op_de_wachtlijst_houdt_zijn_plek_als_een_onbekende_eigenaar_een_lid_krijgt(app):
    # Alleen een andere eigenaar haalt de boot eraf (besluit 2026-11-01); onbekend naar lid verandert niemand.
    anna, bram = lid(), lid("1002", "Bram")
    o, b = onbekend(), boot(anna.id, "Kajak", "Fuut")
    wachtlijst.erop_zetten(o.id, None, CLI)
    wachtlijst.erop_zetten(b.id, None, CLI)
    wijzig(o, lid_id=anna.id)
    wijzig(b, lid_id=bram.id)
    assert o.wachtlijst is not None and b.wachtlijst is None


def test_eigenaar_kiezen_alleen_zolang_de_eigenaar_onbekend_is(app):
    anna = lid()
    o = onbekend()
    boten.eigenaar_kiezen(o.id, anna.id, CLI)
    assert o.lid_id == anna.id
    with pytest.raises(Regelfout, match="heeft intussen een eigenaar"):
        boten.eigenaar_kiezen(o.id, None, CLI, clubboot=True)
    assert o.clubboot is False  # de tweede keuze is niet toegepast


def test_eigenaar_kiezen_weigert_geen_keuze_oud_lid_en_onbekend_lid(app):
    oud = lid("1002", "Oud", opzegdatum=vandaag())
    o = onbekend()
    with pytest.raises(Regelfout, match="Kies een eigenaar"):
        boten.eigenaar_kiezen(o.id, None, CLI)
    with pytest.raises(Regelfout, match="intussen opgezegd"):
        boten.eigenaar_kiezen(o.id, oud.id, CLI)
    with pytest.raises(Regelfout, match="bestaat niet"):
        boten.eigenaar_kiezen(o.id, 424242, CLI)
    assert (o.lid_id, o.clubboot) == (None, False)


def test_zonder_eigenaar_alleen_onbekende_op_naam_en_het_aantal(app):
    boot(lid().id, "Kajak", "Lid")
    boot(None, "Kajak", "Club")
    onbekend("Zeemeeuw"), onbekend("Aalscholver")
    assert [b.naam for b in boten.zonder_eigenaar()] == ["Aalscholver", "Zeemeeuw"]
    assert boten.aantal_zonder_eigenaar() == 2


def test_api_clubboot_is_true_alleen_bij_een_clubboot(app):
    """#212: eigenaar blijft null bij clubboot en onbekend; clubboot onderscheidt ze. Een mutant
    die clubboot afleidt uit `lid is None` laat Wulp true geven en valt hier."""
    toewijzing.toewijzen(plaats("A/1/1").id, (o := onbekend("Wulp")).id, CLI)
    boot(None, "Kajak", "Club")
    boot(lid().id, "Kajak", "Eigen")
    uit = {b["naam"]: b for b in uitlezen.boten()}
    assert {k: (v["eigenaar"], v["clubboot"]) for k, v in uit.items()} == {
        "Wulp": (None, False), "Club": (None, True),
        "Eigen": ({"lidnummer": "1001", "naam": "Anna de Vries"}, False)}
    assert all(set(b) == {"id", "naam", "bootsoort", "plaats", "eigenaar", "clubboot"}
               for b in uit.values())
    assert uit["Wulp"]["plaats"] == "A/1/1" and o.clubboot is False


# Schermen


def test_pagina_boten_zonder_eigenaar_een_regel_per_boot_met_label_en_knop(ingelogd):  # noqa: F811
    toewijzing.toewijzen(plaats("A/1/1").id, onbekend("Wulp").id, CLI)
    onbekend("Kluut")
    lid()
    boot(None, "Kajak", "Clubboot")
    html = ingelogd.get("/boten/zonder-eigenaar").text
    assert "2 boten zonder eigenaar" in html and "Clubboot" not in html.split('<ul class="bl-lijst">')[1]
    items = re.findall(r'<li class="bl-item">(.*?)</li>', html, re.DOTALL)
    assert len(items) == 2
    wulp = next(i for i in items if "Wulp" in i)
    assert ">A/1/1</a>" in wulp and "Eigenaar van Wulp</label>" in wulp
    assert ">Eigenaar opslaan: Wulp</button>" in wulp and "Kluut" not in wulp
    assert "geen plaats" in next(i for i in items if "Kluut" in i)
    assert '<option value="" selected>Geen keuze</option>' in wulp and "(clubboot)" in wulp
    assert "Anna de Vries (1001)" in wulp and 'value="onbekend"' not in wulp


def test_pagina_boten_zonder_eigenaar_leeg(ingelogd):  # noqa: F811
    boot(None, "Kajak", "Clubboot")
    html = ingelogd.get("/boten/zonder-eigenaar").text
    assert "Alle boten hebben een eigenaar." in html and "bl-lijst" not in html


def test_bootnaam_wordt_geescaped_op_boten_zonder_eigenaar(ingelogd):  # noqa: F811
    # Mutant: |safe op de bootnaam in lijst, label of knop valt hier.
    onbekend("<b>x</b>")
    html = ingelogd.get("/boten/zonder-eigenaar").text
    assert "<b>x</b>" not in html and html.count("&lt;b&gt;x&lt;/b&gt;") == 3  # titel, label en knop


def test_menu_toont_het_aantal_in_de_link_en_bij_nul_alleen_de_naam(ingelogd):  # noqa: F811
    link = re.compile(r'<a class="dj-nav__link" href="/boten/zonder-eigenaar"[^>]*>(.*?)</a>', re.DOTALL)
    assert link.search(ingelogd.get("/rekoverzicht").text).group(1) == "Boten zonder eigenaar"
    onbekend("Wulp"), onbekend("Kluut")
    assert link.search(ingelogd.get("/rekoverzicht").text).group(1) == (
        'Boten zonder eigenaar <span class="ds-tag ds-tag--telling bl-nav__aantal">2</span>')
    # na Wachtlijst, onder Dagelijks
    namen = re.findall(r'class="dj-nav__link"[^>]*>([^<]+)', ingelogd.get("/rekoverzicht").text)
    assert namen.index("Boten zonder eigenaar ") == namen.index("Wachtlijst") + 1


def test_menu_item_is_gemarkeerd_op_de_eigen_pagina(ingelogd):  # noqa: F811
    assert re.search(r'href="/boten/zonder-eigenaar" aria-current="page"', ingelogd.get("/boten/zonder-eigenaar").text)


def test_openbare_pagina_en_login_tellen_de_boten_niet(client, app, monkeypatch):
    onbekend()
    monkeypatch.setattr(boten, "aantal_zonder_eigenaar", lambda: pytest.fail("telling zonder beheerder"))
    assert client.get("/inloggen").status_code == 200  # geen beheerder: geen menu en geen telling


def test_boot_met_onbekende_eigenaar_hernoemen_via_het_formulier(ingelogd):  # noqa: F811
    o = onbekend()
    ingelogd.post(f"/boten/{o.id}", data={"naam": "Wulp 2", "bootsoort": o.bootsoort_id, "eigenaar": "onbekend"})
    db.session.expire_all()
    o = db.session.get(Boot, o.id)
    assert (o.naam, o.lid_id, o.clubboot) == ("Wulp 2", None, False)


def test_eigenaar_opslaan_gelukt_ook_clubboot_op_gewone_plaats_en_raakt_alleen_die_boot(ingelogd):  # noqa: F811
    anna = lid()
    toewijzing.toewijzen(plaats("A/1/1").id, (kluut := onbekend("Kluut")).id, CLI)
    wulp = onbekend("Wulp")
    onbekend("Waterhoen")
    r = ingelogd.post(f"/boten/{kluut.id}/eigenaar", data={"eigenaar": "club"}, follow_redirects=True)
    assert "De eigenaar van Kluut is opgeslagen." in r.text and "Wulp" in r.text  # #205
    r = ingelogd.post(f"/boten/{wulp.id}/eigenaar", data={"eigenaar": str(anna.id)}, follow_redirects=True)
    assert "De eigenaar van Wulp is opgeslagen." in r.text
    assert wulp.lid_id == anna.id and kluut.lid_id is None and kluut.clubboot is True
    assert "1 boot zonder eigenaar" in r.text


@pytest.mark.parametrize("waarde", ["", "onbekend", "abc"], ids=["leeg", "onbekend-niet-aangeboden", "tekst"])
def test_eigenaar_opslaan_zonder_geldige_keuze_vraagt_een_eigenaar(ingelogd, waarde):  # noqa: F811
    o = onbekend()
    r = ingelogd.post(f"/boten/{o.id}/eigenaar", data={"eigenaar": waarde}, follow_redirects=True)
    assert "Kies een eigenaar." in r.text and (o.lid_id, o.clubboot) == (None, False)


def test_eigenaar_opslaan_voor_een_boot_die_niet_bestaat_is_404(ingelogd):  # noqa: F811
    assert ingelogd.post("/boten/424242/eigenaar", data={"eigenaar": "club"}).status_code == 404


def test_eigenaar_opslaan_vraagt_inloggen(client, app):
    o = onbekend()
    assert client.post(f"/boten/{o.id}/eigenaar", data={"eigenaar": "club"}).status_code in (302, 401, 403)
    assert o.clubboot is False


# Nieuwe boot (#207)


def test_nieuwe_boot_staat_bovenaan_en_dicht_met_eigenaar_onbekend_eerst(ingelogd):  # noqa: F811
    lid()
    html = ingelogd.get("/boten").text
    assert re.search(r'<h1>Boten</h1>\s*<details class="bl-nieuw">\s*<summary id="nieuw-kop">Nieuwe boot</summary>', html)
    assert html.index('id="nieuw-kop"') < html.index('id="boten-zoek"')
    opties = re.findall(r"<option value=\"([^\"]*)\"[^>]*>([^<]*)</option>",
                        html.split('id="eigenaar"')[1].split("</select>")[0])
    assert opties == [("onbekend", "eigenaar onbekend"), ("club", "Botenloods (clubboot)"),
                      ("1", "Anna de Vries (1001)")]
    assert 'value="onbekend" selected' in html and "Kies een eigenaar</option>" not in html


@pytest.mark.parametrize("eigenaar, verwacht", [("onbekend", (None, False)), ("club", (None, True)), ("lid", (1, False))])
def test_nieuwe_boot_zonder_eigenaar_is_onbekend_met_lid_en_vereniging_zoals_voorheen(ingelogd, eigenaar, verwacht):  # noqa: F811
    # Mutant: onbekend als clubboot opslaan (de oude regel) valt op de eerste parameter.
    anna = lid()
    waarde = str(anna.id) if eigenaar == "lid" else eigenaar
    ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": waarde})
    b = db.session.scalar(select(Boot))
    assert (b.lid_id and 1, b.clubboot) == verwacht


@pytest.mark.parametrize("waarde", ["", "abc"], ids=["leeg", "ongeldig"])
def test_nieuwe_boot_met_lege_of_ongeldige_eigenaar_geeft_kies_een_eigenaar(ingelogd, waarde):  # noqa: F811
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": waarde}, follow_redirects=True)
    assert "Kies een eigenaar." in r.text and db.session.scalar(select(Boot)) is None


# Andere schermen met een eigenaar


def test_boot_toont_onbekend_en_biedt_de_keuze_bij_elke_boot(ingelogd):  # noqa: F811
    o, club, eigen = onbekend("Wulp"), boot(None, "Kajak", "Club"), boot(lid().id, "Kajak", "Eigen")
    plaats("A/1/1")
    html = ingelogd.get(f"/boten/{o.id}").text
    assert re.search(r"<dt>Eigenaar</dt> <dd>onbekend</dd>", html)
    assert '<option value="onbekend" selected>eigenaar onbekend</option>' in html
    assert "Vrije plaats voor kajak" in html and "clubplaats" not in html and "Een clubboot kan niet" not in html
    assert "Op de wachtlijst zetten" in html
    # #233; mutant: de optie weer alleen bij een onbekende boot valt hier. Niet geselecteerd bij een eigenaar.
    for b in (club, eigen):
        assert '<option value="onbekend">eigenaar onbekend</option>' in ingelogd.get(f"/boten/{b.id}").text


def test_boot_met_onbekende_eigenaar_kiest_uit_gewone_plaatsen(ingelogd):  # noqa: F811
    plaats("A/1/1"), plaats("A/1/2", club=True)
    html = ingelogd.get(f"/boten/{onbekend().id}").text
    assert "A/1/1 (rek A)" in html and "A/1/2 (rek A)" not in html


def test_lijsten_en_indeling_noemen_eigenaar_onbekend_en_geen_clubboot(ingelogd):  # noqa: F811
    toewijzing.toewijzen(plaats("A/1/1").id, onbekend("Wulp").id, CLI)
    boten_html = ingelogd.get("/boten").text
    assert '<span data-label="Eigenaar">eigenaar onbekend</span>' in boten_html and "clubboot</span>" not in boten_html
    indeling_html = ingelogd.get("/indeling").text
    assert 'data-label="Eigenaar">eigenaar onbekend</td>' in indeling_html
    assert "Wulp (eigenaar onbekend)" in ingelogd.get("/rekoverzicht").text


def test_wachtlijst_scherm_toont_een_boot_met_onbekende_eigenaar(ingelogd):  # noqa: F811
    wachtlijst.erop_zetten(onbekend("Wulp").id, None, CLI)
    html = ingelogd.get("/wachtlijst").text
    assert "Wulp" in html and '<span data-label="Eigenaar">eigenaar onbekend</span>' in html
    plaats("A/1/1")
    assert "Wulp (Kajak, eigenaar onbekend, sinds" in ingelogd.get("/plaatsen/1").text


def test_toets_design_system_plaats_en_wachtlijst(ingelogd):  # noqa: F811
    """Toets Design System op blok 5: op Plaats staat onder Eigenaar alleen "onbekend", en de
    uitleg van de wachtlijst noemt geen leden meer, want ook een boot zonder eigenaar kan erop."""
    p = plaats("A/1/1")
    toewijzing.toewijzen(p.id, onbekend("Wulp").id, CLI)
    html = ingelogd.get(f"/plaatsen/{p.id}").text
    assert "<p>onbekend</p>" in html and "<p>eigenaar onbekend</p>" not in html
    assert "<p>Boten zonder plaats, per bootsoort," in ingelogd.get("/wachtlijst").text


def test_indeling_export_noemt_eigenaar_onbekend(ingelogd):  # noqa: F811
    import io

    from openpyxl import load_workbook
    toewijzing.toewijzen(plaats("A/1/1").id, onbekend("Wulp").id, CLI)
    blad = load_workbook(io.BytesIO(ingelogd.get("/indeling.xlsx").data)).active
    assert [c.value for c in list(blad.iter_rows())[1]][4:] == ["Wulp", "eigenaar onbekend", None]


def test_gelijktijdig_eigenaar_kiezen_ziet_de_eerdere_keuze(app):
    """Een andere sessie geeft de boot net een lid; met het slot ziet eigenaar_kiezen dat en weigert."""
    anna = lid()
    o = onbekend()
    fouten = race(app, ["SELECT id FROM boot WHERE id = :b FOR UPDATE", "UPDATE boot SET lid_id = :l WHERE id = :b"],
                  {"b": o.id, "l": anna.id}, lambda: boten.eigenaar_kiezen(o.id, None, CLI, clubboot=True))
    assert len(fouten) == 1 and "heeft intussen een eigenaar" in fouten[0], fouten
    assert (db.session.get(Boot, o.id).lid_id, db.session.get(Boot, o.id).clubboot) == (anna.id, False)
