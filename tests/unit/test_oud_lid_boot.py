"""Een boot van een oud-lid vastleggen en een plaats geven (#298, BLB-005, BLB-046). Eén regel voor de
bewaartermijn: opzegdatum, of uit_bron_op als die ontbreekt; precies 5 jaar valt er nog binnen, 5 jaar
en 1 dag erbuiten. Ledenimport en opschonen staan hier en in test_opschonen.py. Tests rekenen met
`vandaag()`, niet met vaste jaartallen."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.domein import CLI, Regelfout, boten, leden, lidkeuze, toewijzing, vandaag, wachtlijst
from app.models import Boot, Lid, Logregel, Taakrun, db
from tests.unit.hulp import als_api, lid
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats
from tests.unit.test_overzichten_en_instellingen import opzeggen
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture

DAG = timedelta(days=1)
VELDEN = ["opzegdatum", "uit_bron_op"]
# De twee kanten van de grens: precies 5 jaar blijft binnen de termijn, 5 jaar en 1 dag valt erbuiten.
BINNEN, BUITEN = 0, 1


def grens():
    return leden.jaren_terug(vandaag(), leden.BEWAARJAREN)


def begin(dagen_voor_grens):
    return grens() - dagen_voor_grens * DAG


def oud_lid(dagen_voor_grens=BINNEN, nummer="2001", naam="Oud Lid", veld="opzegdatum"):
    return lid(nummer, naam, **{veld: begin(dagen_voor_grens)})


def nummers(lijst):
    return [x.lidnummer for x in lijst]


def logreden(actie):
    return [r.gegevens.get("reden") for r in db.session.scalars(select(Logregel).where(Logregel.actie == actie))]


# De gedeelde regel


@pytest.mark.parametrize("dagen,buiten", [(-2000, False), (-1, False), (0, False), (1, True), (None, False)],
                         ids=["toekomst", "jonger", "precies_5_jaar", "5_jaar_en_1_dag", "geen_begin"])
def test_buiten_termijn_heeft_de_grens_aan_beide_kanten(app, dagen, buiten):
    # Mutant: `<` in `<=` valt op precies_5_jaar; `>=` op de andere gevallen.
    assert leden.buiten_termijn(None if dagen is None else begin(dagen)) is buiten


def test_buiten_termijn_rekent_met_de_opgegeven_dag(app):
    assert leden.buiten_termijn(vandaag(), vandaag() + 2000 * DAG) and not leden.buiten_termijn(vandaag())


def test_opzegdatum_gaat_voor_uit_bron_op(app):
    # Mutant: `or` omdraaien (uit_bron_op eerst) valt op de eerste assert.
    nieuw_en_oud = Lid(lidnummer="1", naam="x", opzegdatum=vandaag(), uit_bron_op=begin(BUITEN))
    alleen_oud = Lid(lidnummer="2", naam="x", uit_bron_op=begin(BUITEN))
    assert not leden.lid_buiten_termijn(nieuw_en_oud) and leden.lid_buiten_termijn(alleen_oud)


def test_sql_en_python_geven_dezelfde_uitkomst(app):
    """`termijn_verlopen` (query) en `buiten_termijn` (object) zijn één regel: elke combinatie van
    opzegdatum en uit_bron_op, ook leeg. Mutant: de grens in één van beide veranderen valt hier."""
    waarden = [None, begin(BUITEN), begin(BINNEN), vandaag() + DAG]
    for i, (opz, bron) in enumerate((o, b) for o in waarden for b in waarden):
        lid(f"{3000 + i}", f"Lid {i}", opzegdatum=opz, uit_bron_op=bron)
    alle = db.session.scalars(select(Lid)).all()
    assert len(alle) == 16
    binnen = {x.lidnummer for x in alle if not leden.lid_buiten_termijn(x)}
    assert binnen and binnen != {x.lidnummer for x in alle}
    assert set(nummers(leden.actieve_leden(met_oud=True))) == binnen


# Keuze (lidkeuze, BV-85, BV-86)


def test_kiesbare_leden_met_oud_geeft_ook_de_oud_leden_binnen_de_termijn(app):
    # Mutant: `oud` negeren valt op de tweede assert; de grens in de query op de derde.
    lid("1001", "Anna Actief")
    oud_lid(BINNEN, "1002", "Anna Opzegdatum")
    oud_lid(BINNEN, "1003", "Anna Bron", "uit_bron_op")
    oud_lid(BUITEN, "1004", "Anna Buiten")
    oud_lid(BUITEN, "1005", "Anna Bron Buiten", "uit_bron_op")
    assert nummers(lidkeuze.kiesbare_leden("Anna")) == ["1001"]
    assert nummers(lidkeuze.kiesbare_leden("Anna", oud=True)) == ["1001", "1003", "1002"]


def test_veld_en_lid_van_waarde_vragen_oud_apart(app):
    # Mutant: oud=True als standaard in `veld` valt op de eerste assert (de bezettingsimport vraagt het niet).
    oud = oud_lid(BINNEN, "1002", "Anna Oud")
    lid("1001", "Anna Actief")
    assert [t.waarde for t in lidkeuze.veld("Anna").treffers] == ["1001"]
    treffers = lidkeuze.veld("Anna", oud=True).treffers
    assert [(t.waarde, t.oud) for t in treffers] == [("1001", False), ("1002", True)]
    assert lidkeuze.lid_van_waarde(oud.lidnummer) is None
    assert lidkeuze.lid_van_waarde(oud.lidnummer, oud=True).id == oud.id
    assert lidkeuze.lid_van_waarde(oud_lid(BUITEN, "1003", "Anna Buiten").lidnummer, oud=True) is None


@pytest.mark.parametrize("dagen,gelukt", [(BINNEN, True), (BUITEN, False)], ids=["precies_5_jaar", "5_jaar_en_1_dag"])
def test_eigenaar_van_een_formulier_accepteert_een_oud_lid_binnen_de_termijn(app, dagen, gelukt):
    # Mutant: lid_van_waarde(keuze) zonder oud=True in lidkeuze.eigenaar valt op precies_5_jaar.
    oud = oud_lid(dagen)
    uitkomst, veld = lidkeuze.eigenaar(oud.lidnummer, "")
    if gelukt:
        assert uitkomst == (oud.id, False) and veld is None
    else:
        assert uitkomst is None and veld.fout == lidkeuze.ONGELDIG


# Boot aanmaken, wijzigen, eigenaar kiezen


@pytest.mark.parametrize("veld", VELDEN)
def test_boot_voor_oud_lid_binnen_de_termijn_wordt_vastgelegd(app, veld):
    # Mutant: de oude is_oud_lid-controle terugzetten valt hier.
    oud = oud_lid(BINNEN, veld=veld)
    b = boot(oud.id)
    assert b.lid_id == oud.id and acties() == ["boot.aangemaakt"]


@pytest.mark.parametrize("veld", VELDEN)
def test_boot_voor_oud_lid_buiten_de_termijn_geweigerd(app, veld):
    # Mutant: de controle in _boot_aanmaken weglaten valt hier.
    oud = oud_lid(BUITEN, veld=veld)
    with pytest.raises(Regelfout, match="is meer dan 5 jaar oud-lid en krijgt geen nieuwe boot"):
        boot(oud.id)
    assert db.session.scalar(select(Boot)) is None and acties() == []


def wijzig(b, **velden):
    return boten.boot_wijzigen(b.id, velden.get("naam", b.naam), b.bootsoort_id, velden.get("lid_id", b.lid_id),
                               CLI, clubboot=False)


def test_boot_wijzigen_naar_een_oud_lid_binnen_de_termijn_en_niet_erbuiten(app):
    # Mutant: de controle in boot_wijzigen weglaten valt op de Regelfout; is_oud_lid terug op de eerste assert.
    anna = lid()
    b = boot(anna.id)
    binnen, buiten = oud_lid(BINNEN), oud_lid(BUITEN, "2002", "Te Oud")
    with pytest.raises(Regelfout, match="Te Oud is meer dan 5 jaar oud-lid"):
        wijzig(b, lid_id=buiten.id)
    assert b.lid_id == anna.id
    wijzig(b, lid_id=binnen.id)
    assert b.lid_id == binnen.id


def test_een_bestaande_eigenaar_buiten_de_termijn_blijft_staan_bij_een_andere_naam(app):
    # Mutant: de voorwaarde `lid_id != b.lid_id` weghalen valt hier.
    anna = lid()
    b = boot(anna.id)
    oud = oud_lid(BINNEN)
    wijzig(b, lid_id=oud.id)
    opzeggen(oud.id, opzegdatum=begin(BUITEN))
    wijzig(b, naam="Fuut")
    assert (b.lid_id, b.naam) == (oud.id, "Fuut")
    wijzig(b, lid_id=anna.id)  # er weer vanaf mag
    assert b.lid_id == anna.id


# Wachtlijst (besluit 27)


def test_boot_op_de_wachtlijst_met_een_oud_lid_als_eigenaar_gaat_eraf_met_reden_oud_lid(app):
    # Mutant: de tak `oud-lid` weglaten laat de boot staan (eerste assert); de reden "andere eigenaar"
    # valt op de tweede.
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    wijzig(b, lid_id=oud_lid().id)
    assert b.wachtlijst is None and logreden("wachtlijst.verwijderd") == ["oud-lid"]


def test_onbekende_boot_op_de_wachtlijst_gaat_eraf_als_hij_een_oud_lid_krijgt(app):
    # Mutant: de voorwaarde `lid_id != oud_lid_id and oud_lid_id is not None` voor het oud-lid laten
    # staan valt hier: de eigenaar was onbekend.
    wulp = boot(None, "Kajak", "Wulp", onbekend=True)
    wachtlijst.erop_zetten(wulp.id, None, CLI)
    wijzig(wulp, lid_id=oud_lid().id)
    assert wulp.wachtlijst is None and logreden("wachtlijst.verwijderd") == ["oud-lid"]


def test_boot_op_de_wachtlijst_met_een_actief_lid_als_nieuwe_eigenaar_houdt_de_andere_reden(app):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    wijzig(b, lid_id=lid("1002", "Bram").id)
    assert logreden("wachtlijst.verwijderd") == ["andere eigenaar"]


@pytest.mark.parametrize("dagen", [BINNEN, BUITEN], ids=["precies_5_jaar", "5_jaar_en_1_dag"])
def test_een_oud_lid_mag_niet_op_de_wachtlijst_ook_niet_binnen_de_termijn(app, dagen):
    # Mutant: erop_zetten op lid_buiten_termijn laten rekenen valt op precies_5_jaar.
    oud = oud_lid(dagen)
    b = Boot(naam="Fuut", bootsoort_id=1, lid_id=oud.id)  # de boot bestond al voor de opzegging
    db.session.add(b)
    db.session.commit()
    with pytest.raises(Regelfout, match="is oud-lid. De boot kan niet op de wachtlijst"):
        wachtlijst.erop_zetten(b.id, None, CLI)
    assert b.wachtlijst is None


# Plaats toewijzen


def boot_van_oud_lid(dagen, naam="Fuut"):
    """De boot bestond al voor de opzegging: aangemaakt voor een lid, dat daarna opzegt."""
    anna = lid("2001", "Oud Lid")
    b = boot(anna.id, naam=naam)
    opzeggen(anna.id, opzegdatum=begin(dagen))
    return b


def test_een_boot_van_een_oud_lid_binnen_de_termijn_krijgt_een_plaats(app):
    # Mutant: is_oud_lid terug in _toewijzen valt hier.
    p, b = plaats(), boot_van_oud_lid(BINNEN)
    toewijzing.toewijzen(p.id, b.id, CLI)
    assert p.boot_id == b.id and toewijzing.past(p, b)


def test_een_boot_van_een_oud_lid_buiten_de_termijn_krijgt_geen_plaats(app):
    # Mutant: de controle in _toewijzen weglaten valt op de Regelfout; in past() op de laatste assert.
    p, b = plaats(), boot_van_oud_lid(BUITEN)
    with pytest.raises(Regelfout, match="meer dan 5 jaar oud-lid. De boot krijgt geen plaats"):
        toewijzing.toewijzen(p.id, b.id, CLI)
    assert p.boot_id is None and not toewijzing.past(p, b)


def test_een_boot_van_een_oud_lid_krijgt_geen_clubplaats(app):
    # Besluit 2. De regel staat in controleer_past (alleen clubboten op een clubplaats); mutant: die
    # regel weglaten valt hier.
    club, b = plaats(club=True), boot_van_oud_lid(BINNEN)
    with pytest.raises(Regelfout, match="clubplaats en alleen voor clubboten"):
        toewijzing.toewijzen(club.id, b.id, CLI)
    assert club.boot_id is None and not toewijzing.past(club, b)


@pytest.mark.parametrize("dagen", [BINNEN, BUITEN], ids=["binnen", "buiten"])
def test_een_boot_van_een_oud_lid_mag_verplaatsen_ook_buiten_de_termijn(app, dagen):
    # Vraag 11. Mutant: de oude controle in verplaatsen terugzetten valt op `buiten`.
    p, b = plaats(), boot(lid("2001", "Oud Lid").id, naam="Fuut")
    toewijzing.toewijzen(p.id, b.id, CLI)
    opzeggen(b.lid_id, opzegdatum=begin(dagen))
    nieuw = plaats("A/1/2")
    assert toewijzing.verplaatsen(b.id, nieuw.id, CLI) == "A/1/2"
    assert nieuw.boot_id == b.id and p.boot_id is None


# Bootaantallen (vraag 10)


def test_bootaantallen_laat_oud_leden_weg_ook_met_een_plaats(app):
    # Mutant: over alle leden lopen valt hier; ook de teller van de statuspagina.
    actief = lid("1001", "Anna Actief")
    toewijzing.toewijzen(plaats().id, boot(actief.id).id, CLI)
    oud = oud_lid(BINNEN, "1002", "Anna Oud")
    toewijzing.toewijzen(plaats("A/1/2").id, boot(oud.id, naam="Fuut").id, CLI)
    assert [r["lidnummer"] for r in boten.bootaantallen()] == ["1001"]
    assert boten.bootaantallen()[0]["aantallen"]["Kajak"] == 1
    boten.bootaantallen_ophalen()
    assert db.session.scalar(select(Taakrun.aantallen).where(Taakrun.taak == boten.BOOTAANTALLEN)) == {"leden": 1}


# Ledenimport (besluit 3)


OPZEGDATUMS = {"geen_opzegdatum": (lambda: None, True), "morgen": (lambda: vandaag() + DAG, True),
               "gisteren": (lambda: vandaag() - DAG, True), "precies_5_jaar": (lambda: begin(BINNEN), True),
               "5_jaar_en_1_dag": (lambda: begin(BUITEN), False)}


@pytest.mark.parametrize("naam", OPZEGDATUMS)
def test_import_neemt_een_nieuw_oud_lid_alleen_binnen_de_termijn_op(app, naam):
    # Mutant: `<` in `<=` in leden.buiten_termijn valt op precies_5_jaar; de oude controle (opzegdatum <= dag)
    # terug valt op gisteren en precies_5_jaar.
    datum, nieuw = OPZEGDATUMS[naam]
    opzegdatum = datum()
    record = {"lidnummer": "9001", "naam": "Nieuw Oud", "lid_sinds": "2010-01-01",
              "opzegdatum": opzegdatum and opzegdatum.isoformat()}
    aantallen = als_api(leden.importeer, [record], CLI)
    assert aantallen["nieuw"] == int(nieuw) and aantallen["overgeslagen"] == int(not nieuw)
    assert (db.session.scalar(select(Lid).where(Lid.lidnummer == "9001")) is not None) is nieuw


# Web


def eigenaar_veld(tekst):
    return tekst.split('<fieldset class="dj-choices"', 1)[1].split("</fieldset>", 1)[0]


def test_treffers_tonen_de_tag_oud_lid_achter_het_label_en_escapen_de_naam(ingelogd):  # noqa: F811
    # Mutant: `|safe` op de naam laat <b>x</b> door; de tag weglaten valt op de eerste assert; een tag bij
    # een actief lid op de derde.
    oud_lid(BINNEN, "1002", "Oud <b>x</b>")
    lid("1001", "Actief <b>x</b>")
    r = ingelogd.post("/boten", data={"actie": "zoeken", "naam": "Fuut", "bootsoort": "1", "zoek": "<b>x</b>"})
    veld = eigenaar_veld(r.text)
    assert "Oud &lt;b&gt;x&lt;/b&gt; (1002) <span class=\"ds-tag\">oud-lid</span></label>" in veld
    assert "<b>x</b>" not in r.text
    assert "Actief &lt;b&gt;x&lt;/b&gt; (1001)</label>" in veld and veld.count("ds-tag") == 1


def test_nieuwe_boot_met_een_oud_lid_binnen_de_termijn_wordt_vastgelegd_en_buiten_niet(ingelogd):  # noqa: F811
    binnen, buiten = oud_lid(BINNEN), oud_lid(BUITEN, "2002", "Te Oud")
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": buiten.lidnummer})
    assert r.status_code == 422 and lidkeuze.ONGELDIG in r.text and db.session.scalar(select(Boot)) is None
    r = ingelogd.post("/boten", data={"naam": "Fuut", "bootsoort": "1", "eigenaar": binnen.lidnummer})
    db.session.expire_all()
    assert r.status_code == 302 and db.session.scalar(select(Boot)).lid_id == binnen.id


def test_boot_wijzigen_toont_de_melding_bij_een_oud_lid_en_zoekt_oud_leden(ingelogd):  # noqa: F811
    oud = oud_lid(BINNEN, "2001", "Oud Lid")
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    r = ingelogd.post(f"/boten/{b.id}", data={"actie": "zoeken", "naam": b.naam, "bootsoort": "1", "zoek": "Oud Lid"})
    assert 'ds-tag">oud-lid</span></label>' in r.text  # Mutant: oud=True in _na_zoeken weglaten valt hier
    r = ingelogd.post(f"/boten/{b.id}", data={"naam": b.naam, "bootsoort": "1", "eigenaar": oud.lidnummer},
                      follow_redirects=True)
    db.session.expire_all()
    assert b.lid_id == oud.id and "De eigenaar is oud-lid. De boot is van de wachtlijst gehaald." in r.text


def test_leden_toont_lid_en_oud_lid_in_dezelfde_kolom_en_escapet(ingelogd):  # noqa: F811
    # Mutant: `|safe` op l.naam laat <b>x</b> door; de tag weer achter de naam valt op de assert van rij_oud (#362).
    oud = oud_lid(BINNEN, "1002", "Oud <b>x</b>")
    actief = lid("1001", "Actief")
    t = ingelogd.get("/leden").text
    assert "<b>x</b>" not in t and "Oud &lt;b&gt;x&lt;/b&gt;</a>" in t
    rij_oud = t.split(f'href="/leden/{oud.id}"', 1)[1].split("</li>", 1)[0]
    assert '<p class="bl-item__zijde"><span class="ds-tag" data-label="Status">oud-lid</span></p>' in rij_oud
    rij_actief = t.split(f'href="/leden/{actief.id}"', 1)[1].split("</li>", 1)[0]
    assert '<p class="bl-item__zijde"><span class="ds-tag" data-label="Status">lid</span></p>' in rij_actief
    assert t.count('data-label="Status">oud-lid') == 1


def taak(tekst):
    return tekst.split('class="kaart bl-taak"', 1)[1].split("</section>", 1)[0]


def test_bootpagina_van_een_oud_lid_binnen_de_termijn_heeft_plaats_toewijzen_en_geen_wachtlijst(ingelogd):  # noqa: F811
    # Mutant: verwijderen_in_taak op oud_lid in plaats van buiten_termijn valt op de eerste assert; het blok
    # `elif oud_lid` weglaten op de tweede.
    plaats()
    b = boot_van_oud_lid(BINNEN)
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert ">Plaats toewijzen</h2>" in t and 'name="plaats_id"' in t and "Boot verwijderen" not in t
    assert "Een oud-lid kan niet op de wachtlijst." in t and "Op de wachtlijst zetten" not in t


def test_bootpagina_van_een_oud_lid_op_de_wachtlijst_toont_de_taaktekst_van_besluit_31(ingelogd):  # noqa: F811
    anna = lid("2001", "Oud Lid")
    b = boot(anna.id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    opzeggen(anna.id, opzegdatum=vandaag())
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert "De eigenaar is oud-lid. Bij de volgende ledenimport gaat de boot van de wachtlijst." in t
    assert "Van de wachtlijst halen" in t


def test_bootpagina_van_een_oud_lid_buiten_de_termijn_zonder_plaats_heeft_boot_verwijderen(ingelogd):  # noqa: F811
    b = boot_van_oud_lid(BUITEN)
    t = taak(ingelogd.get(f"/boten/{b.id}").text)
    assert ">Boot verwijderen</h2>" in t and 'name="plaats_id"' not in t
    assert "De eigenaar is al meer dan 5 jaar oud-lid. De boot krijgt geen plaats" in t


def test_bootpagina_van_een_oud_lid_buiten_de_termijn_met_plaats_heeft_het_blok_verplaatsen(ingelogd):  # noqa: F811
    # Vraag 11. Mutant: `and not oud_lid` terug in boot.html valt hier.
    b = boot(lid("2001", "Oud Lid").id, naam="Fuut")
    toewijzing.toewijzen(plaats("A/1/1").id, b.id, CLI)
    plaats("A/1/2")
    opzeggen(b.lid_id, opzegdatum=begin(BUITEN))
    tekst = ingelogd.get(f"/boten/{b.id}").text
    assert "Boot verplaatsen</summary>" in tekst and 'id="verplaats-plaats"' in tekst
