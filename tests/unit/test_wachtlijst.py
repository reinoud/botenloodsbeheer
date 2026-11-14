"""Wachtlijst per bootsoort (BLB-013), toewijzen vanaf de lijst (BLB-014), vrijgeven zonder
automatische toewijzing (BLB-011 criterium 3) en de lijst per lid (BLB-019 criterium 1).
De import die boten van oud-leden van de lijst haalt, staat in test_leden.py (BLB-008, #27)."""

import re
from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError

from app.domein import CLI, Actor, Regelfout, boten, leden, log, toewijzing, vandaag, wachtlijst
from app.models import Boot, Logregel, Plaats, Wachtlijst, db
from tests.unit.hulp import lid, race
from tests.unit.test_boot_wijzigen import BOOTSLOT, wijzig
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats, soort
from tests.unit.test_web_beheer import ingelogd  # noqa: F401 (fixture)

ANNA = Actor("beheerder", 1, "anna")


def regels(actie=None):
    db.session.expire_all()
    q = select(Logregel).order_by(Logregel.id)
    if actie:
        q = q.where(Logregel.actie == actie)
    return db.session.scalars(q).all()


def op_lijst(b):
    db.session.expire_all()
    return db.session.get(Wachtlijst, b.id)


# Erop zetten en de aanmelddatum (BLB-013 criteria 1, 2 en 7; besluit stakeholder 2026-11-01)


def test_zonder_datum_vandaag_met_logregel(app):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, None, ANNA)
    assert op_lijst(b).aangemeld_op == vandaag()
    [r] = regels("wachtlijst.toegevoegd")
    assert (r.actor_naam, r.verwijzingen) == ("anna", [f"boot:{b.id}", f"lid:{b.lid_id}"])
    assert r.gegevens == {"boot": "Zeemeeuw", "bootsoort": "Kajak",
                          "aangemeld_op": vandaag().isoformat()}


def test_lege_datum_is_vandaag(app):
    """Het formulierveld stuurt een lege string; alleen None als leeg zien weigert die."""
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "", CLI)
    assert op_lijst(b).aangemeld_op == vandaag()


@pytest.mark.parametrize("dagen", [0, 1, 3650], ids=["vandaag", "gisteren", "tien_jaar_terug"])
def test_vandaag_of_eerder_mag_en_staat_in_het_log(app, dagen):
    """Grens: vandaag mag (deze test), morgen niet (test_morgen_in_de_tijdzone_...)."""
    b = boot(lid().id)
    dag = vandaag() - timedelta(days=dagen)
    wachtlijst.erop_zetten(b.id, dag.isoformat(), CLI)
    assert op_lijst(b).aangemeld_op == dag
    assert regels("wachtlijst.toegevoegd")[0].gegevens["aangemeld_op"] == dag.isoformat()


@pytest.mark.parametrize("waarde, melding", [
    ((date.today() + timedelta(days=2)).isoformat(), "mag niet in de toekomst"),
    ("31-12-2025", "geldige aanmelddatum"), ("morgen", "geldige aanmelddatum"),
], ids=["overmorgen", "verkeerd_formaat", "tekst"])
def test_toekomst_of_onleesbare_datum_geweigerd(app, waarde, melding):
    b = boot(lid().id)
    with pytest.raises(Regelfout, match=melding):
        wachtlijst.erop_zetten(b.id, waarde, CLI)
    assert op_lijst(b) is None and not regels("wachtlijst.toegevoegd")


def test_morgen_in_de_tijdzone_van_de_installatie_geweigerd(app, monkeypatch):
    """De grens is vandaag() van de installatie, niet de datum van de server."""
    b = boot(lid().id)
    monkeypatch.setattr(wachtlijst, "vandaag", lambda: date(2026, 3, 1))
    with pytest.raises(Regelfout, match="toekomst"):
        wachtlijst.erop_zetten(b.id, date(2026, 3, 2), CLI)
    wachtlijst.erop_zetten(b.id, date(2026, 3, 1), CLI)
    assert op_lijst(b).aangemeld_op == date(2026, 3, 1)


def test_aanmelddatum_niet_te_wijzigen_ook_niet_in_de_database(app):
    """Intake: een andere datum kan alleen door eraf te halen en er opnieuw op te zetten."""
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "2024-01-01", CLI)
    with pytest.raises(Regelfout, match="staat al op de wachtlijst"):
        wachtlijst.erop_zetten(b.id, "2023-01-01", CLI)
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(Wachtlijst.__table__.update().values(aangemeld_op=date(2020, 1, 1)))
    db.session.rollback()
    wachtlijst.eraf_halen(b.id, CLI)
    wachtlijst.erop_zetten(b.id, "2023-01-01", CLI)
    assert op_lijst(b).aangemeld_op == date(2023, 1, 1)


# Weigeringen (BLB-013 criteria 3 en 5)


def test_clubboot_geweigerd_met_reden(app):
    b = boot(None)
    with pytest.raises(Regelfout, match="is een clubboot. Een clubboot kan niet op de wachtlijst"):
        wachtlijst.erop_zetten(b.id, None, CLI)
    assert op_lijst(b) is None


@pytest.mark.parametrize("veld", ["opzegdatum", "uit_bron_op"])
def test_boot_van_oud_lid_geweigerd_met_reden(app, veld):
    oud = lid("2001", "Oud Lid", **{veld: vandaag() - timedelta(days=1)})
    b = Boot(naam="Fuut", bootsoort_id=soort("Kajak"), lid_id=oud.id)  # van vóór de opzegging
    db.session.add(b)
    db.session.commit()
    with pytest.raises(Regelfout, match="is oud-lid. De boot kan niet op de wachtlijst"):
        wachtlijst.erop_zetten(b.id, None, CLI)
    assert op_lijst(b) is None and not regels("wachtlijst.toegevoegd")


def test_lid_met_opzegdatum_in_de_toekomst_mag_erop(app):
    b = boot(lid(opzegdatum=vandaag() + timedelta(days=1)).id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    assert op_lijst(b) is not None


def test_boot_met_plaats_of_al_op_de_lijst_geweigerd(app):
    p = plaats()
    b, c = boot(lid().id), boot(lid("1002").id, naam="Fuut")
    toewijzing.toewijzen(p.id, b.id, CLI)
    with pytest.raises(Regelfout, match="Boot Zeemeeuw heeft al een plaats"):
        wachtlijst.erop_zetten(b.id, None, CLI)
    wachtlijst.erop_zetten(c.id, None, CLI)
    with pytest.raises(Regelfout, match="Boot Fuut staat al op de wachtlijst"):
        wachtlijst.erop_zetten(c.id, None, CLI)
    assert op_lijst(b) is None and len(regels("wachtlijst.toegevoegd")) == 1


def test_onbekende_boot_geweigerd(app):
    with pytest.raises(Regelfout, match="bestaat niet"):
        wachtlijst.erop_zetten(999, None, CLI)
    with pytest.raises(Regelfout, match="staat niet op de wachtlijst"):
        wachtlijst.eraf_halen(999, CLI)


# Eraf halen (BLB-013 criteria 6 en 7)


def test_eraf_halen_met_logregel_bij_de_bootmutaties(app):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "2025-05-01", CLI)
    wachtlijst.eraf_halen(b.id, ANNA)
    assert op_lijst(b) is None
    [r] = regels("wachtlijst.verwijderd")
    assert r.gegevens == {"boot": "Zeemeeuw", "aangemeld_op": "2025-05-01"}
    assert r.verwijzingen == [f"boot:{b.id}", f"lid:{b.lid_id}"]
    with pytest.raises(Regelfout, match="staat niet op de wachtlijst"):
        wachtlijst.eraf_halen(b.id, CLI)
    # BLB-043: onder de boot en in /log, niet in het technische log
    assert [r.actie for r in log.regels([f"boot:{b.id}"])] == [
        "wachtlijst.verwijderd", "wachtlijst.toegevoegd", "boot.aangemaakt"]
    assert not [r for r in log.regels(technisch=True) if r.actie.startswith("wachtlijst.")]


# De lijsten (BLB-013 criterium 4)


def test_lijst_per_bootsoort_langst_wachtende_bovenaan(app):
    a, b = lid("1001", "Anna"), lid("1002", "Bram")
    k1 = boot(a.id, naam="Kajak nieuw")
    k2 = boot(b.id, naam="Kajak oud")
    s1 = boot(a.id, bootsoort="Surfski", naam="Surfski")
    wachtlijst.erop_zetten(k1.id, "2025-06-01", CLI)
    wachtlijst.erop_zetten(k2.id, "2023-02-01", CLI)
    wachtlijst.erop_zetten(s1.id, "2024-01-01", CLI)
    lijsten = [(s.naam, [w.boot.naam for w in rij]) for s, rij in wachtlijst.lijsten()]
    assert lijsten == [("Kajak", ["Kajak oud", "Kajak nieuw"]), ("Surfski", ["Surfski"])]


def test_oud_lid_niet_meer_op_de_lijst_getoond(app, monkeypatch):
    """Een opzegdatum die na het erop zetten verstrijkt: de import haalt hem eraf (test_leden),
    tot dan toont de lijst hem niet."""
    b = boot(lid(opzegdatum=vandaag() + timedelta(days=1)).id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    assert len(wachtlijst.lijsten()) == 1
    morgen = vandaag() + timedelta(days=1)
    monkeypatch.setattr(leden, "vandaag", lambda: morgen)
    assert wachtlijst.lijsten() == []


@pytest.mark.parametrize("aangemeld, tekst", [
    (date(2026, 3, 1), "0 dagen"), (date(2026, 2, 28), "1 dag"), (date(2026, 2, 2), "27 dagen"),
    (date(2026, 2, 1), "1 maand"), (date(2025, 12, 15), "2 maanden"),
    (date(2025, 3, 1), "1 jaar"), (date(2023, 1, 31), "3 jaar en 1 maand"),
], ids=["vandaag", "1_dag", "net_geen_maand", "precies_een_maand", "maanden", "jaar",
        "jaren_en_maand"])
def test_wachttijd(aangemeld, tekst):
    assert wachtlijst.wachttijd(aangemeld, date(2026, 3, 1)) == tekst


# Toewijzen vanaf de lijst (BLB-014) en vrijgeven (BLB-011 criterium 3)


def test_toewijzen_haalt_de_boot_van_de_lijst_met_logregel(app):
    p = plaats()
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "2024-04-01", CLI)
    toewijzing.toewijzen(p.id, b.id, ANNA)
    assert op_lijst(b) is None and db.session.get(Plaats, p.id).boot_id == b.id
    assert [r.actie for r in log.regels([f"boot:{b.id}"])][:2] == ["wachtlijst.verwijderd",
                                                                   "plaats.toegewezen"]
    assert regels("wachtlijst.verwijderd")[0].gegevens["reden"] == "plaats toegewezen"


def test_ongeschikte_plaats_geweigerd_en_boot_blijft_op_de_lijst(app):
    p = plaats(soorten=("Surfski",))
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "2024-04-01", CLI)
    with pytest.raises(Regelfout, match="niet geschikt voor een kajak"):
        toewijzing.toewijzen(p.id, b.id, CLI)
    assert op_lijst(b).aangemeld_op == date(2024, 4, 1) and not regels("wachtlijst.verwijderd")


def test_vrijgegeven_plaats_blijft_vrij_ook_met_een_wachtlijst(app):
    p = plaats()
    b, c = boot(lid().id), boot(lid("1002").id, naam="Fuut")
    toewijzing.toewijzen(p.id, b.id, CLI)
    wachtlijst.erop_zetten(c.id, "2020-01-01", CLI)
    toewijzing.vrijgeven(p.id, CLI)
    assert db.session.get(Plaats, p.id).boot_id is None and op_lijst(c) is not None
    assert [r.actie for r in regels()][-1] == "plaats.vrijgegeven"


# Boot wijzigen en verwijderen: afgeleid uit het model


def test_andere_bootsoort_verhuist_naar_die_lijst_met_dezelfde_datum(app):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "2024-04-01", CLI)
    wijzig(b, bootsoort="Surfski")
    [(s, [w])] = wachtlijst.lijsten()
    assert (s.naam, w.aangemeld_op) == ("Surfski", date(2024, 4, 1))


def test_andere_eigenaar_haalt_de_boot_van_de_lijst_met_reden(app):
    oud = lid()
    b = boot(oud.id)
    nieuw = lid("1002")
    wachtlijst.erop_zetten(b.id, "2024-01-01", CLI)
    wijzig(b, lid_id=nieuw.id, actor=ANNA)
    assert op_lijst(b) is None
    [r] = regels("wachtlijst.verwijderd")
    assert r.gegevens == {"boot": "Zeemeeuw", "aangemeld_op": "2024-01-01", "reden": "andere eigenaar"}
    assert r.verwijzingen == [f"boot:{b.id}", f"lid:{oud.id}"] and r.actor_naam == "anna"
    assert acties()[-2:] == ["wachtlijst.verwijderd", "boot.gewijzigd"]


def test_zelfde_eigenaar_houdt_de_boot_op_de_lijst(app):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, "2024-01-01", CLI)
    wijzig(b, naam="Fuut")
    assert op_lijst(b).aangemeld_op == date(2024, 1, 1) and not regels("wachtlijst.verwijderd")


def test_boot_op_de_lijst_wordt_geen_clubboot(app):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    with pytest.raises(Regelfout, match="staat op de wachtlijst. Een clubboot kan daar niet op"):
        wijzig(b, lid_id=None)
    assert db.session.get(Boot, b.id).lid_id is not None


def test_verwijderde_boot_gaat_van_de_lijst(app):
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    boten.boot_verwijderen(b.id, CLI)
    assert db.session.scalar(select(Wachtlijst)) is None


# Gelijktijdigheid: erop zetten vergrendelt de boot, net als toewijzen


def test_gelijktijdig_toewijzen_en_erop_zetten(app):
    """Zonder het slot op de boot ziet erop_zetten de toewijzing niet en krijgt de boot een
    plaats en een plek op de lijst."""
    p = plaats()
    b = boot(lid().id)
    fouten = race(app, [BOOTSLOT, "UPDATE plaats SET boot_id = :b WHERE id = :p"],
                  {"p": p.id, "b": b.id}, lambda: wachtlijst.erop_zetten(b.id, None, CLI))
    assert fouten == ["Boot Zeemeeuw heeft al een plaats."] and op_lijst(b) is None


def test_gelijktijdig_twee_keer_erop_zetten(app):
    b = boot(lid().id)
    fouten = race(app, [BOOTSLOT, "INSERT INTO wachtlijst VALUES (:b, '2024-01-01')"],
                  {"b": b.id}, lambda: wachtlijst.erop_zetten(b.id, None, CLI))
    assert fouten == ["Boot Zeemeeuw staat al op de wachtlijst."]
    assert op_lijst(b).aangemeld_op == date(2024, 1, 1)


def test_gelijktijdig_eraf_halen_en_toewijzen(app):
    """Toewijzen (eerste sessie, slot op de boot) haalt de boot van de lijst; eraf_halen wacht
    en meldt netjes dat de boot er niet meer op staat."""
    b = boot(lid().id)
    wachtlijst.erop_zetten(b.id, None, CLI)
    fouten = race(app, [BOOTSLOT, "DELETE FROM wachtlijst WHERE boot_id = :b"], {"b": b.id},
                  lambda: wachtlijst.eraf_halen(b.id, CLI))
    assert fouten == ["Deze boot staat niet op de wachtlijst."]
    assert db.session.get(Wachtlijst, b.id) is None


# Schermen


def test_schermen_wachtlijst_boot_en_lid(ingelogd):  # noqa: F811
    anna = lid()
    b, c = boot(anna.id), boot(anna.id, naam="Fuut")
    r = ingelogd.post(f"/boten/{b.id}/wachtlijst", data={"aangemeld_op": "2024-03-01"},
                      follow_redirects=True)
    assert "De boot staat op de wachtlijst." in r.text and "sinds 01-03-2024" in r.text
    morgen = (vandaag() + timedelta(days=1)).isoformat()
    r = ingelogd.post(f"/boten/{c.id}/wachtlijst", data={"aangemeld_op": morgen},
                      follow_redirects=True)
    assert "mag niet in de toekomst" in r.text and op_lijst(c) is None
    r = ingelogd.get("/wachtlijst").text
    assert "Zeemeeuw" in r and "Anna de Vries" in r and "01-03-2024" in r
    assert "wachtlijst toegevoegd" in r  # bootmutaties onder de wachtlijst
    lidpagina = ingelogd.get(f"/leden/{anna.id}").text  # BLB-019 criterium 1
    assert "Sinds 01-03-2024" in lidpagina and lidpagina.count("Wachtlijst: ") == 1  # alleen bij de boot op de lijst
    r = ingelogd.post(f"/boten/{b.id}/wachtlijst/verwijderen", data={"terug": "wachtlijst"})
    assert r.location.endswith("/wachtlijst") and op_lijst(b) is None


def test_clubboot_toont_reden_in_plaats_van_formulier(ingelogd):  # noqa: F811
    b = boot(None)
    r = ingelogd.get(f"/boten/{b.id}").text
    assert "Een clubboot kan niet op de wachtlijst." in r and "Op de wachtlijst zetten" not in r


def test_plaats_toont_wachtenden_voor_passende_soort_eerst(ingelogd):  # noqa: F811
    p = plaats()
    k = boot(lid().id, naam="Kievit")
    s = boot(lid("1002").id, bootsoort="Surfski", naam="Snoek")
    boot(lid("1003").id, naam="Otter")
    wachtlijst.erop_zetten(k.id, "2024-01-01", CLI)
    wachtlijst.erop_zetten(s.id, "2020-01-01", CLI)  # past niet op deze plaats
    r = ingelogd.get(f"/plaatsen/{p.id}").text
    wachtend, overig = r.split("Andere boten zonder plaats")
    assert "Kievit" in wachtend and "sinds 01-01-2024" in wachtend
    assert "Otter" in overig and "Kievit" not in overig
    assert "Snoek" not in r  # #131: een surfski past niet op deze plaats


def test_clubplaats_toont_geen_wachtenden(ingelogd):  # noqa: F811
    p = plaats(club=True)
    wachtlijst.erop_zetten(boot(lid().id, naam="Kievit").id, None, CLI)
    r = ingelogd.get(f"/plaatsen/{p.id}").text
    assert "Op de wachtlijst, langst wachtend eerst" not in r


def test_andere_eigenaar_geeft_een_melding_aan_de_beheerder(ingelogd):  # noqa: F811
    b = boot(lid().id)
    nieuw = lid("1002")
    wachtlijst.erop_zetten(b.id, None, CLI)
    r = ingelogd.post(f"/boten/{b.id}", data={"naam": "Zeemeeuw", "bootsoort": soort("Kajak"),
                                              "eigenaar": nieuw.id}, follow_redirects=True)
    assert "van de wachtlijst gehaald" in r.text and op_lijst(b) is None
    r = ingelogd.post(f"/boten/{b.id}", data={"naam": "Fuut", "bootsoort": soort("Kajak"),
                                              "eigenaar": nieuw.id}, follow_redirects=True)
    assert "van de wachtlijst gehaald" not in r.text


def test_bezoeker_kan_wachtlijst_niet_zien_of_wijzigen(client):
    b = boot(lid().id)
    assert client.get("/wachtlijst").location.endswith("/inloggen")
    for pad in (f"/boten/{b.id}/wachtlijst", f"/boten/{b.id}/wachtlijst/verwijderen"):
        assert client.post(pad).location.endswith("/inloggen")
    assert op_lijst(b) is None


def test_keuzelijst_alleen_met_boten_die_toewijzen_accepteert(ingelogd):  # noqa: F811
    """#131: de regels van toewijzen; elke uitgesloten boot zou toewijzen weigeren."""
    p, club = plaats(), plaats("A/1/2", club=True)
    boot(lid().id, naam="Kievit")
    boot(None, naam="Clubkajak")
    oud = lid("1002", opzegdatum=vandaag())  # de boot bestond al voor de opzegging
    db.session.add(Boot(naam="Oudje", bootsoort_id=soort("Kajak"), lid_id=oud.id))
    db.session.commit()
    r = ingelogd.get(f"/plaatsen/{p.id}").text
    assert "Kievit" in r and "Clubkajak (Kajak, clubboot)" in r and "Oudje" not in r  # #205
    r = ingelogd.get(f"/plaatsen/{club.id}").text
    assert "Clubkajak" in r and "Kievit" not in r and "Oudje" not in r
    leeg = plaats("A/1/3", soorten=("Surfski",))
    r = ingelogd.get(f"/plaatsen/{leeg.id}").text
    assert "Er zijn geen boten zonder plaats die op deze plaats passen." in r
    assert 'name="boot_id"' not in r


# Toewijzen vanaf de bootpagina (#132)


def test_bootpagina_toont_alleen_vrije_passende_plaatsen_in_volgorde_van_de_loods(ingelogd):  # noqa: F811
    tweede, eerste = plaats("A/2/1"), plaats("A/1/1")  # aangemaakt in omgekeerde volgorde
    plaats("A/1/2", soorten=("Surfski",))
    club = plaats("A/1/3", club=True)
    bezet = plaats("A/1/4")
    toewijzing.toewijzen(bezet.id, boot(lid().id, naam="Bezetter").id, CLI)
    b = boot(lid("1002").id, naam="Kievit")
    r = ingelogd.get(f"/boten/{b.id}").text
    keuzes = r.split('name="plaats_id"')[1].split("</select>")[0]
    assert keuzes.index("A/1/1") < keuzes.index("A/2/1")
    assert eerste.code in keuzes and tweede.code in keuzes
    assert "A/1/2" not in keuzes and "A/1/3" not in keuzes and "A/1/4" not in keuzes
    assert "Wijs toe aan plek" in r
    assert "<optgroup" not in keuzes  # een ledenboot: één lijst zonder groepen (BV-74)
    # Besluit stakeholder 2026-11-10 (BV-74, #205): een clubboot kiest uit twee groepen, clubplaatsen eerst.
    # Mutant: vrije_plaatsen zonder ook_club valt op de volgorde; zonder de groepen op de optgroup.
    c = boot(None, naam="Clubkajak")
    r = ingelogd.get(f"/boten/{c.id}").text
    keuzes = r.split('name="plaats_id"')[1].split("</select>")[0]
    groepen = re.findall(r'<optgroup label="([^"]+)">(.*?)</optgroup>', keuzes, re.DOTALL)
    assert [g for g, _ in groepen] == ["Clubplaatsen", "Gewone plaatsen"]
    assert club.code in groepen[0][1] and "A/1/1" not in groepen[0][1]
    assert groepen[1][1].index("A/1/1") < groepen[1][1].index("A/2/1")
    assert "A/1/2" not in keuzes and "A/1/4" not in keuzes  # verkeerde soort, bezet
    assert "Vrije plaats voor kajak" in r and "Vrije clubplaats" not in r


def test_bootpagina_van_een_clubboot_laat_een_lege_groep_weg(ingelogd):  # noqa: F811
    club = plaats("A/1/1", club=True)
    c = boot(None, naam="Clubkajak")
    keuzes = ingelogd.get(f"/boten/{c.id}").text.split('name="plaats_id"')[1].split("</select>")[0]
    assert 'label="Clubplaatsen"' in keuzes and "Gewone plaatsen" not in keuzes and club.code in keuzes
    toewijzing.toewijzen(club.id, c.id, CLI)
    gewoon = plaats("A/1/2")
    d = boot(None, naam="Tweede")
    keuzes = ingelogd.get(f"/boten/{d.id}").text.split('name="plaats_id"')[1].split("</select>")[0]
    assert 'label="Gewone plaatsen"' in keuzes and "Clubplaatsen" not in keuzes and gewoon.code in keuzes


def test_bootpagina_van_een_clubboot_zonder_vrije_plaats_zegt_dat_zonder_aparte_melding(ingelogd):  # noqa: F811
    plaats("A/1/1", soorten=("Surfski",), club=True)
    c = boot(None, naam="Clubkajak")
    r = ingelogd.get(f"/boten/{c.id}").text
    assert "Er is geen vrije plaats voor kajak." in r and "<optgroup" not in r and "lubplaats" not in r


def test_clubboot_toewijzen_aan_een_gewone_plaats_via_de_bootpagina(ingelogd):  # noqa: F811
    p, c = plaats(), boot(None, naam="Clubkajak")
    r = ingelogd.post(f"/boten/{c.id}/toewijzen", data={"plaats_id": p.id}, follow_redirects=True)
    assert "De boot heeft de plaats gekregen." in r.text
    db.session.expire_all()
    assert db.session.get(Plaats, p.id).boot_id == c.id


def test_toewijzen_vanaf_bootpagina_haalt_boot_van_de_wachtlijst(ingelogd):  # noqa: F811
    p = plaats()
    b = boot(lid().id, naam="Kievit")
    wachtlijst.erop_zetten(b.id, "2024-03-01", CLI)
    r = ingelogd.post(f"/boten/{b.id}/toewijzen", data={"plaats_id": p.id}, follow_redirects=True)
    assert "De boot heeft de plaats gekregen." in r.text
    assert f">{p.code}</a>" in r.text and 'name="plaats_id"' not in r.text
    db.session.expire_all()
    assert db.session.get(Plaats, p.id).boot_id == b.id
    assert op_lijst(b) is None
    assert "plaats.toegewezen" in acties() and "wachtlijst.verwijderd" in acties()


def test_toewijzen_vanaf_bootpagina_weigert_bezet_en_niet_passend(ingelogd):  # noqa: F811
    bezet, surfski = plaats(), plaats("A/1/2", soorten=("Surfski",))
    toewijzing.toewijzen(bezet.id, boot(lid().id, naam="Bezetter").id, CLI)
    b = boot(lid("1002").id, naam="Kievit")
    for p, melding in ((bezet, "is al bezet"), (surfski, "niet geschikt voor een kajak")):
        aantal = len(acties())
        r = ingelogd.post(f"/boten/{b.id}/toewijzen", data={"plaats_id": p.id},
                          follow_redirects=True)
        assert melding in r.text
        assert len(acties()) == aantal
    db.session.expire_all()
    assert db.session.get(Boot, b.id).plaats is None


def test_bootpagina_zonder_keuzelijst_met_plaats_zonder_vrije_plaats_of_oud_lid(ingelogd):  # noqa: F811
    p = plaats()
    met = boot(lid().id, naam="Bezetter")
    toewijzing.toewijzen(p.id, met.id, CLI)
    r = ingelogd.get(f"/boten/{met.id}").text
    assert 'name="plaats_id"' not in r and "Plaats toewijzen" not in r
    plaats("A/1/2", soorten=("Surfski",))
    zonder = boot(lid("1002").id, naam="Kievit")
    r = ingelogd.get(f"/boten/{zonder.id}").text
    assert 'name="plaats_id"' not in r and "Er is geen vrije plaats voor kajak." in r
    plaats("A/1/3")
    oud = lid("1003", opzegdatum=vandaag())  # de boot bestond al voor de opzegging
    db.session.add(Boot(naam="Oudje", bootsoort_id=soort("Kajak"), lid_id=oud.id))
    db.session.commit()
    oudje = db.session.scalar(select(Boot).where(Boot.naam == "Oudje"))
    r = ingelogd.get(f"/boten/{oudje.id}").text
    assert 'name="plaats_id"' not in r and "De eigenaar is oud-lid. De boot krijgt geen plaats en kan niet op de wachtlijst." in r


def test_bootpagina_zonder_plaats_geeft_200(ingelogd):  # noqa: F811
    """#137: een boot op de wachtlijst, een clubboot en een boot van een oud-lid, alle zonder plaats."""
    plaats(), plaats("A/1/2", club=True)
    kievit = boot(lid().id, naam="Kievit")
    wachtlijst.erop_zetten(kievit.id, "2024-03-01", CLI)
    # Na de aanmelding opgezegd: tot de volgende import staat de boot nog op de lijst.
    oudje = Boot(naam="Oudje", bootsoort_id=soort("Kajak"), lid_id=lid("1002", opzegdatum=vandaag()).id)
    db.session.add_all([oudje, Wachtlijst(boot=oudje, aangemeld_op=date(2024, 3, 1))])
    db.session.commit()
    for b in (kievit, oudje, boot(None, naam="Clubkajak")):
        assert ingelogd.get(f"/boten/{b.id}").status_code == 200


def test_bezoeker_kan_niet_toewijzen_vanaf_bootpagina(client):
    p, b = plaats(), boot(lid().id, naam="Kievit")
    assert client.post(f"/boten/{b.id}/toewijzen", data={"plaats_id": p.id}).location.endswith(
        "/inloggen")
    db.session.expire_all()
    assert db.session.get(Plaats, p.id).boot_id is None
