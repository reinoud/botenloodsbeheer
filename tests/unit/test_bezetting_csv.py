"""Bezetting exporteren en importeren als CSV (issue #158, ADR-014 §1, §3 en §4): formaat, rondgang,
elke uitkomst en elke foutsoort, koppelen, bevestigen als alles of niets, de vergrendelingen, de
onthouden koppelingen, de opschoning en de webroutes. De migratie en de rechten staan in
test_bezetting_csv_migratie.py."""

import threading
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import OperationalError

from app.domein import (
    CLI,
    Actor,
    Regelfout,
    bezetting_csv,
    boten,
    indeling,
    log,
    toewijzing,
    wachtlijst,
)
from app.domein.csvbestand import CsvFout
from app.models import (
    Bezettingsimport,
    Boot,
    Bootsoort,
    Logregel,
    Naamkoppeling,
    Plaats,
    Rek,
    Wachtlijst,
    db,
)
from tests.unit.conftest import WEB
from tests.unit.hulp import beheerder_met_wachtwoord, lid, race
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats, soort
from tests.unit.test_tokens import eigenaar
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture

KOP = "plaats;boot;bootsoort;eigenaar;lidnummer"


@pytest.fixture
def actor(app):
    """De beheerder die uploadt: bezettingsimport.beheerder_id is een echte beheerder."""
    b, _geheim = beheerder_met_wachtwoord("uploader")
    return Actor.van(b)


def bestand(*regels, kop=KOP, bom=True):
    """Een CSV-bestand als bytes, standaard UTF-8 met BOM zoals de export. De kopregel is regel 1."""
    tekst = "\r\n".join([kop, *regels]) + "\r\n"
    return (("﻿" if bom else "") + tekst).encode("utf-8")


def leg(code, naam="Zeemeeuw", lid_id=None, bootsoort="Kajak", soorten=("Kajak",), club=False):
    """Een plaats met een boot erop. Geeft (plaats, boot)."""
    p = plaats(code, soorten, club or lid_id is None)
    b = boot(lid_id, bootsoort, naam)
    toewijzing.toewijzen(p.id, b.id, CLI)
    return p, b


def beoordeling(data, actor, keuzes=None):
    """Uploadt, bewaart eventuele keuzes en geeft de uitkomst per regelnummer."""
    bezetting_csv.uploaden(data, actor)
    if keuzes:
        bezetting_csv.koppelen(keuzes, actor)
    return {u.regel: u for u in bezetting_csv.overzicht()["uitkomsten"]}


def stand():
    """Alles wat een bevestiging mag wijzigen: boten, plaatsen, wachtlijst en bootmutaties."""
    db.session.expire_all()
    return (
        [(b.id, b.naam, b.bootsoort_id, b.lid_id) for b in db.session.scalars(select(Boot).order_by(Boot.id))],
        [(p.id, p.boot_id) for p in db.session.scalars(select(Plaats).order_by(Plaats.id))],
        [w.boot_id for w in db.session.scalars(select(Wachtlijst))],
        len(log.regels(limiet=1000)),
    )


def technisch(actie="bezetting.geimporteerd"):
    return db.session.scalars(select(Logregel).where(Logregel.actie == actie)
                              .order_by(Logregel.id)).all()


def regel_van(u):
    return u.uitkomst, u.melding


def alleen_regelfouten(actie, anders):
    """race() vangt alleen Regelfouten; een andere fout laat de thread stil sterven. Die komt
    hier in anders, zodat de test hem ziet."""
    def omhuld():
        try:
            actie()
        except Regelfout:
            raise
        except Exception as fout:  # noqa: BLE001
            anders.append(repr(fout))

    return omhuld


# Export en sjabloon


def test_export_zonder_bezette_plaatsen_is_bom_en_kopregel(app):
    plaats("A/1/1")
    assert bezetting_csv.export() == b"\xef\xbb\xbf" + KOP.encode() + b"\r\n"


def test_export_een_regel_per_bezette_plaats_in_de_volgorde_van_de_loods(app):
    anna = lid("1001", "Anna de Vries")
    leg("B/1/1", "Reiger", anna.id)  # B is het eerste rek, A het tweede
    leg("A/1/1", "Clubkajak")
    leg("A/2/1", "Fuut", anna.id, "Surfski", ("Surfski",))
    plaats("A/1/2")  # vrij: geen regel
    regels = bezetting_csv.export().decode("utf-8-sig").split("\r\n")[:-1]
    assert regels == [KOP, "B/1/1;Reiger;Kajak;Anna de Vries;1001", "A/1/1;Clubkajak;Kajak;;",
                      "A/2/1;Fuut;Surfski;Anna de Vries;1001"]


def test_lege_export_is_een_sjabloon_met_uitleg_en_voorbeelden_en_importeren_weigert_het(app, actor):
    data = bezetting_csv.export(leeg=True)
    regels = data.decode("utf-8-sig").splitlines()
    assert data.startswith(b"\xef\xbb\xbf") and regels[-1] == KOP
    assert all(r.startswith("#") for r in regels[:-1])
    tekst = "\n".join(regels)
    assert "Kajak, Canadese kano, Surfski, C11, Supboard" in tekst
    assert "# Voorbeeld: A/1/1;Zeemeeuw;Kajak;Anna de Vries;1001" in regels
    assert "# Voorbeeld clubboot: B/1/1;Clubkajak;Kajak;;" in regels
    assert "beide leeg" in tekst and "niets tot je bevestigt" in tekst
    with pytest.raises(Regelfout, match="geen regels"):
        bezetting_csv.uploaden(data, actor)
    assert db.session.scalar(select(Bezettingsimport)) is None


def test_export_weigert_een_rek_dat_met_hekje_begint(app):
    r = Rek(naam="#oud")
    db.session.add_all([r, Plaats(rek=r, verdieping=1, vak=1, publieke_sleutel="x" * 10,
                                  boot=Boot(naam="Reiger", bootsoort_id=soort("Kajak")))])
    db.session.commit()
    with pytest.raises(Regelfout, match="#oud begint met #"):
        bezetting_csv.export()


def test_export_weigert_een_stuurteken_in_een_naam_en_het_scherm_slaat_het_niet_op(app):
    _p, b = leg("A/1/1")
    eigenaar("UPDATE boot SET naam = :n WHERE id = :i", n="Zee\nmeeuw", i=b.id)
    db.session.expire_all()
    with pytest.raises(Regelfout, match="stuurteken"):
        bezetting_csv.export()
    with pytest.raises(Regelfout, match="zonder stuurtekens"):
        boten.boot_aanmaken("Zee\tmeeuw", soort("Kajak"), None, None, CLI)
    with pytest.raises(Regelfout, match="zonder stuurtekens"):
        boten.boot_wijzigen(b.id, "Zee\x07meeuw", soort("Kajak"), None, CLI)


# Rondgang


def rondgang_wereld():
    """Een ledenboot, een clubboot, de boot van een oud-lid en een formulecel, op plaatsen die niet
    de standaardwaarden hebben (een clubplaats, een plaats met twee bootsoorten)."""
    anna, oud = lid("1001", "Anna de Vries"), lid("1002", "Oud Lid")
    leg("A/1/1", "Reiger", anna.id, soorten=("Kajak", "Surfski"))
    leg("A/1/2", "=1+1", anna.id)  # een formule: de export zet er een ' voor
    leg("A/1/3", "Clubkajak")
    leg("B/1/1", "Fuut", oud.id)
    eigenaar("UPDATE lid SET opzegdatum = '2020-01-01' WHERE id = :i", i=oud.id)
    plaats("B/1/2")


def test_rondgang_export_ongewijzigd_importeren_geeft_alles_ongewijzigd_en_verandert_niets(app, actor):
    rondgang_wereld()
    data = bezetting_csv.export()
    assert b"'=1+1" in data and b"Oud Lid;1002" in data
    voor = stand()
    uitkomst = beoordeling(data, actor)
    assert {regel_van(u) for u in uitkomst.values()} == {("ongewijzigd", "")}
    assert len(uitkomst) == 4
    assert bezetting_csv.bevestigen(actor) == {
        "regels": 4, "nieuw": 0, "toegewezen": 0, "overschreven": 0, "verplaatst": 0,
        "ongewijzigd": 4, "overgeslagen": 0, "koppelingen": 0}
    assert stand() == voor
    assert db.session.scalar(select(Bezettingsimport)) is None
    assert bezetting_csv.export() == data


# Uploaden en de lopende import


def test_upload_bewaart_de_regels_met_uploader_en_een_verlooptijd_van_twee_uur(app, actor):
    nu = datetime.now(UTC)
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;Anna de Vries;1001", "# commentaar",
                                   "A/1/2;Fuut;Surfski;;"), actor)
    imp = db.session.scalar(select(Bezettingsimport))
    assert imp.beheerder_id == actor.id and imp.keuzes == {}
    assert imp.regels == [
        {"regel": 2, "plaats": "A/1/1", "boot": "Reiger", "bootsoort": "Kajak",
         "eigenaar": "Anna de Vries", "lidnummer": "1001"},
        {"regel": 4, "plaats": "A/1/2", "boot": "Fuut", "bootsoort": "Surfski", "eigenaar": "",
         "lidnummer": ""}]
    assert timedelta(minutes=119) < imp.verloopt_op - nu < timedelta(minutes=121)
    assert bezetting_csv.VERLOOP == timedelta(hours=2)


@pytest.mark.parametrize("data, melding", [
    (bestand("A/1/1;Reiger;Kajak;;;extra"), "Regel 2: 5 kolommen verwacht, 6 gevonden."),
    (bestand("A/1/1;Rei\x07ger;Kajak;;"), "Regel 2: een stuurteken"),
    (bestand("A/1/1;Reiger;Kajak;;", kop="plaats;boot;bootsoort;eigenaar"), "kolom ontbreekt: lidnummer"),
    (b"plaats,boot\r\nA,B\r\n", "geen puntkomma"),
], ids=["kolomtelling", "stuurteken", "kolom-ontbreekt", "scheidingsteken"])
def test_een_fout_in_de_opbouw_van_het_bestand_weigert_alles(app, actor, data, melding):
    with pytest.raises(CsvFout) as fout:
        bezetting_csv.uploaden(data, actor)
    assert melding in " ".join(fout.value.regels)
    assert db.session.scalar(select(Bezettingsimport)) is None


def test_een_bestand_zonder_regels_wordt_geweigerd(app, actor):
    with pytest.raises(Regelfout, match="geen regels"):
        bezetting_csv.uploaden(bestand(), actor)
    assert db.session.scalar(select(Bezettingsimport)) is None


def test_een_tweede_upload_tijdens_een_lopende_import_wordt_geweigerd(app, actor):
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;"), actor)
    with pytest.raises(Regelfout, match="Bevestig of annuleer die eerst"):
        bezetting_csv.uploaden(bestand("A/1/2;Fuut;Kajak;;"), actor)
    assert [r["plaats"] for r in db.session.scalar(select(Bezettingsimport)).regels] == ["A/1/1"]


def test_twee_gelijktijdige_uploads_laten_de_database_een_weigeren(app, actor):
    """De unieke kolom enige, niet alleen de controle in Python: de eerste sessie heeft nog niet
    gecommit, dus de tweede ziet geen lopende import."""
    anders = []
    insert = ("INSERT INTO bezettingsimport (beheerder_id, verloopt_op, regels) VALUES "
              "(:b, now() + interval '2 hours', '[]')")
    upload = alleen_regelfouten(lambda: bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;"), actor), anders)
    fouten = race(app, [insert], {"b": actor.id}, upload)
    assert fouten == ["Er loopt al een bezettingsimport. Bevestig of annuleer die eerst."]
    assert not anders and len(db.session.scalars(select(Bezettingsimport)).all()) == 1


def test_een_verlopen_import_is_weg_voor_upload_overzicht_koppelen_bevestigen_en_annuleren(app, actor):
    def verlopen_upload(code="A/1/1"):
        bezetting_csv.uploaden(bestand(f"{code};Reiger;Kajak;;"), actor)
        eigenaar("UPDATE bezettingsimport SET verloopt_op = now() - interval '1 second'")
        db.session.expire_all()

    verlopen_upload()
    assert bezetting_csv.lopend() is None and bezetting_csv.overzicht() is None
    assert db.session.scalar(select(Bezettingsimport)) is None  # het overzicht ruimde hem op
    for actie in (lambda: bezetting_csv.koppelen({}, actor), lambda: bezetting_csv.bevestigen(actor),
                  lambda: bezetting_csv.annuleren(actor)):
        verlopen_upload()
        with pytest.raises(Regelfout, match="geen bezettingsimport"):
            actie()
    verlopen_upload()
    bezetting_csv.uploaden(bestand("A/1/2;Fuut;Kajak;;"), actor)  # de upload ruimt de oude op
    assert [r["plaats"] for r in db.session.scalar(select(Bezettingsimport)).regels] == ["A/1/2"]


def test_annuleren_haalt_de_import_weg_en_zonder_import_is_het_een_melding(app, actor):
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;"), actor)
    bezetting_csv.annuleren(actor)
    assert db.session.scalar(select(Bezettingsimport)) is None
    with pytest.raises(Regelfout, match="geen bezettingsimport"):
        bezetting_csv.annuleren(actor)


def test_elke_beheerder_kan_de_lopende_import_koppelen_bevestigen_en_annuleren(app, actor):
    """Geen id in de routes: de import is van de hele installatie (ADR-014 §3)."""
    ander = Actor.van(beheerder_met_wachtwoord("collega")[0])
    leg("A/1/1", "Clubkajak")
    bezetting_csv.uploaden(bestand("A/1/1;Clubkajak;Kajak;;"), actor)
    assert bezetting_csv.overzicht()["lopend"].beheerder_id == actor.id
    bezetting_csv.koppelen({"2": "overslaan"}, ander)
    bezetting_csv.bevestigen(ander)
    assert technisch()[0].actor_id == ander.id


# Uitkomsten per regel


@pytest.fixture
def anna(app):
    return lid("1001", "Anna de Vries")


def test_uitkomst_ongewijzigd_toewijzen_overschrijven_verplaatsen_en_nieuwe_boot(app, actor, anna):
    leg("A/1/1", "Reiger", anna.id)  # ongewijzigd
    plaats("A/1/2")
    boot(anna.id, "Kajak", "Fuut")  # toewijzen: vrije plaats, boot zonder plaats
    leg("A/1/3", "Meeuw", anna.id)  # overschrijven: Meeuw gaat van de plaats
    boot(anna.id, "Kajak", "Kievit")
    leg("A/1/4", "Spreeuw", anna.id)  # verplaatsen: naar vrije plaats A/1/5
    plaats("A/1/5")
    plaats("A/1/6")  # nieuwe boot
    uitkomst = beoordeling(bestand(
        "A/1/1;Reiger;Kajak;;1001", "A/1/2;Fuut;Kajak;;1001", "A/1/3;Kievit;Kajak;;1001",
        "A/1/5;Spreeuw;Kajak;;1001", "A/1/6;Nieuwkomer;Kajak;;1001"), actor)
    assert [regel_van(uitkomst[n]) for n in range(2, 7)] == [
        ("ongewijzigd", ""), ("toewijzen", ""), ("overschrijven", "Meeuw gaat van de plaats."),
        ("verplaatsen", "Komt van A/1/4."), ("nieuwe boot", "")]


def test_uitkomst_overschrijven_en_verplaatsen_tegelijk_noemt_beide(app, actor, anna):
    leg("A/1/1", "Reiger", anna.id)
    leg("A/1/2", "Fuut", anna.id)
    uitkomst = beoordeling(bestand("A/1/2;Reiger;Kajak;;1001"), actor)
    assert regel_van(uitkomst[2]) == ("overschrijven", "Fuut gaat van de plaats. Komt van A/1/1.")


def test_uitkomst_nieuwe_boot_op_een_bezette_plaats_noemt_de_boot_die_weggaat(app, actor, anna):
    leg("A/1/1", "Reiger", anna.id)
    uitkomst = beoordeling(bestand("A/1/1;Nieuwkomer;Kajak;;1001"), actor)
    assert regel_van(uitkomst[2]) == ("nieuwe boot", "Reiger gaat van de plaats.")


def test_boot_herkennen_zonder_verschil_in_hoofdletters_en_met_dezelfde_eigenaar(app, actor, anna):
    bert = lid("1002", "Bert Jansen")
    plaats("A/1/1")
    plaats("A/1/2")
    b = boot(anna.id, "Kajak", "Zeemeeuw")
    boot(bert.id, "Kajak", "Zeemeeuw")  # dezelfde naam, andere eigenaar: een andere boot
    uitkomst = beoordeling(bestand("A/1/1;zEEMEEUW;Kajak;;1001", "A/1/2;Zeemeeuw;Kajak;;1003"), actor)
    assert uitkomst[2].boot.id == b.id and uitkomst[2].uitkomst == "toewijzen"
    assert uitkomst[3].uitkomst == "te koppelen"  # lidnummer 1003 bestaat niet, geen naam


def test_overgeslagen_regel_telt_niet_mee_en_een_nieuwe_keuze_draait_het_terug(app, actor, anna):
    plaats("A/1/1")
    plaats("A/1/2")
    data = bestand("A/1/1;Reiger;Kajak;;1001", "A/1/1;Fuut;Kajak;;1001")
    assert beoordeling(data, actor)[3].uitkomst == "fout"  # plaats dubbel
    bezetting_csv.koppelen({"2": "overslaan"}, actor)
    uitkomst = {u.regel: u for u in bezetting_csv.overzicht()["uitkomsten"]}
    assert (uitkomst[2].uitkomst, uitkomst[3].uitkomst) == ("overgeslagen", "nieuwe boot")
    bezetting_csv.koppelen({}, actor)
    assert bezetting_csv.overzicht()["uitkomsten"][0].uitkomst == "nieuwe boot"


FOUTEN = {
    "plaats-leeg": (";Reiger;Kajak;;", "De plaats ontbreekt."),
    "plaats-onbekend-rek": ("Q/1/1;Reiger;Kajak;;", "Plaats Q/1/1 bestaat niet."),
    "plaats-onbekend-vak": ("A/1/9;Reiger;Kajak;;", "Plaats A/1/9 bestaat niet."),
    "plaats-geen-code": ("A11;Reiger;Kajak;;", "Plaats A11 bestaat niet."),
    "plaats-geen-getal": ("A/x/1;Reiger;Kajak;;", "Plaats A/x/1 bestaat niet."),
    "boot-leeg": ("A/1/1;;Kajak;;", "De naam van de boot ontbreekt of is langer dan 100 tekens."),
    "boot-te-lang": (f"A/1/1;{'x' * 101};Kajak;;", "De naam van de boot ontbreekt of is langer"),
    "bootsoort-leeg": ("A/1/1;Reiger;;;", "De bootsoort ontbreekt."),
    "bootsoort-onbekend": ("A/1/1;Reiger;Zeilboot;;", "De bootsoort Zeilboot bestaat niet of is dubbelzinnig"),
    "eigenaar-te-lang": (f"A/1/1;Reiger;Kajak;{'x' * 101};", "De eigenaar is langer dan 100 tekens."),
    "lidnummer-ongeldig": ("A/1/1;Reiger;Kajak;;<b>x</b>", "Het lidnummer is ongeldig."),
    "lidnummer-te-lang": (f"A/1/1;Reiger;Kajak;;{'1' * 21}", "Het lidnummer is ongeldig."),
    "bootsoort-past-niet": ("A/1/1;Reiger;Surfski;;1001",
                            "Plaats A/1/1 is niet geschikt voor een surfski."),
    "clubboot-op-ledenplaats": ("A/1/1;Reiger;Kajak;;", "Boot Reiger is een clubboot en hoort op een clubplaats."),
    "ledenboot-op-clubplaats": ("C/1/1;Reiger;Kajak;;1001",
                                "Plaats C/1/1 is een clubplaats en alleen voor clubboten."),
    "afwijkende-bootsoort": ("A/1/2;Fuut;Surfski;;1001", "Boot Fuut bestaat al als een kajak. De import wijzigt geen boot."),
    "oud-lid-nieuwe-boot": ("A/1/1;Nieuw;Kajak;;1002", "Oud Lid is oud-lid."),
    "oud-lid-bestaande-boot": ("A/1/1;Fuutje;Kajak;;1002", "Oud Lid is oud-lid."),
    "plaats-dubbel": ("A/1/1;Reiger;Kajak;;1001\r\nA/1/1;Aalscholver;Kajak;;1001",
                      "Plaats A/1/1 staat al op regel 2."),
    "boot-dubbel": ("A/1/1;Reiger;Kajak;;1001\r\nA/1/3;reiger;Kajak;;1001", "Deze boot staat al op regel 2."),
    "boot-niet-eenduidig": ("A/1/1;Tweeling;Kajak;;1001", "Er zijn meer boten met deze naam en eigenaar."),
}


@pytest.mark.parametrize("sleutel", FOUTEN)
def test_elke_foutsoort_geeft_de_uitkomst_fout_met_de_reden_en_blokkeert_bevestigen(app, actor, anna, sleutel):
    oud = lid("1002", "Oud Lid")
    plaats("A/1/1")
    plaats("A/1/2")
    plaats("A/1/3")
    plaats("C/1/1", club=True)
    boot(anna.id, "Kajak", "Fuut")
    boot(anna.id, "Kajak", "Tweeling")
    boot(anna.id, "Kajak", "Tweeling")
    boot(oud.id, "Kajak", "Fuutje")  # de boot van een oud-lid zonder plaats
    eigenaar("UPDATE lid SET opzegdatum = '2020-01-01' WHERE id = :i", i=oud.id)
    regels, melding = FOUTEN[sleutel]
    uitkomst = beoordeling(bestand(*regels.split("\r\n")), actor)
    fout = uitkomst[3] if sleutel in ("plaats-dubbel", "boot-dubbel") else uitkomst[2]
    assert fout.uitkomst == "fout" and melding in fout.melding
    voor = stand()
    with pytest.raises(Regelfout, match="regels te koppelen of met een fout"):
        bezetting_csv.bevestigen(actor)
    assert stand() == voor and db.session.scalar(select(Bezettingsimport)) is not None


def test_bootsoort_zonder_verschil_in_hoofdletters_alleen_als_het_er_een_is(app, actor):
    db.session.add_all([Bootsoort(naam="Zee"), Bootsoort(naam="ZEE")])
    db.session.commit()
    plaats("A/1/1", ("Kajak",), club=True)
    uitkomst = beoordeling(bestand("A/1/1;Reiger;kajak;;"), actor)
    assert regel_van(uitkomst[2]) == ("nieuwe boot", "")  # Kajak: één soort zonder hoofdletters
    bezetting_csv.annuleren(actor)
    uitkomst = beoordeling(bestand("A/1/1;Reiger;zee;;"), actor)
    assert uitkomst[2].uitkomst == "fout" and "dubbelzinnig" in uitkomst[2].melding
    bezetting_csv.annuleren(actor)
    assert beoordeling(bestand("A/1/1;Reiger;Zee;;"), actor)[2].uitkomst == "fout"  # precies: Zee past niet


# Eigenaar koppelen


def test_koppelen_volgorde_lidnummer_dan_onthouden_koppeling_dan_exacte_naam(app, actor, anna):
    bert = lid("1002", "Bert Jansen")
    for n in range(1, 8):
        plaats(f"A/1/{n}")
    db.session.add(Naamkoppeling(naam="Bertje", lid_id=bert.id))
    db.session.add(Naamkoppeling(naam="De club", clubboot=True))
    db.session.commit()
    uitkomst = beoordeling(bestand(
        "A/1/1;B1;Kajak;Bert Jansen;1001",  # lidnummer gaat voor naam: Anna
        "A/1/2;B2;Kajak;Bert Jansen;",  # exacte naam: Bert
        "A/1/3;B3;Kajak;Bertje;",  # onthouden koppeling: Bert
        "A/1/4;B4;Kajak;Anna de Vries;9999",  # onbekend lidnummer, dan de naam: Anna
        "A/1/5;B5;Kajak;Bertje;1001",  # lidnummer gaat voor een onthouden koppeling
        "A/1/6;B6;Kajak;De club;",  # onthouden koppeling aan de vereniging
        "A/1/7;B7;Kajak;;",  # leeg is een clubboot
    ), actor)
    assert [(u.lid.id if u.lid else None, u.club, u.via) for u in
            (uitkomst[n] for n in range(2, 9))] == [
        (anna.id, False, "lidnummer"), (bert.id, False, "naam"), (bert.id, False, "koppeling"),
        (anna.id, False, "naam"), (anna.id, False, "lidnummer"), (None, True, "koppeling"),
        (None, True, "")]
    assert uitkomst[8].uitkomst == "fout" and "clubplaats" in uitkomst[8].melding  # B6/B7 op ledenplaats


@pytest.mark.parametrize("eigenaar_naam, lidnummer", [("Onbekend", ""), ("anna de vries", ""),
                                                      (" Anna", ""), ("", "9999"), ("Dubbel Lid", "")],
                         ids=["geen-treffer", "andere-hoofdletters", "deel-van-de-naam", "alleen-onbekend-lidnummer",
                              "twee-treffers"])
def test_zonder_precies_een_treffer_komt_de_regel_in_het_koppelscherm(app, actor, anna, eigenaar_naam, lidnummer):
    lid("2001", "Dubbel Lid")
    lid("2002", "Dubbel Lid")
    plaats("A/1/1")
    u = beoordeling(bestand(f"A/1/1;Reiger;Kajak;{eigenaar_naam};{lidnummer}"), actor)[2]
    assert u.uitkomst == "te koppelen" and not u.lid and not u.club


def test_een_lidnummer_koppelt_ook_een_oud_lid_zodat_de_rondgang_slaagt(app, actor):
    """Zonder lidnummer is een oud-lid met dezelfde naam als een actief lid niet eenduidig."""
    oud = lid("1002", "Anna de Vries")
    lid("1001", "Anna de Vries")
    p = plaats("A/1/1")
    toewijzing.toewijzen(p.id, boot(oud.id, "Kajak", "Fuut").id, CLI)
    eigenaar("UPDATE lid SET opzegdatum = '2020-01-01' WHERE id = :i", i=oud.id)
    assert beoordeling(bestand("A/1/1;Fuut;Kajak;Anna de Vries;1002"), actor)[2].uitkomst == "ongewijzigd"
    bezetting_csv.annuleren(actor)
    assert beoordeling(bestand("A/1/1;Fuut;Kajak;Anna de Vries;"), actor)[2].uitkomst == "te koppelen"


def test_keuze_lid_of_clubboot_koppelt_de_regel_en_overslaan_laat_hem_weg(app, actor, anna):
    plaats("A/1/1")
    plaats("C/1/1", club=True)
    plaats("A/1/2")
    data = bestand("A/1/1;Reiger;Kajak;Onbekend;", "C/1/1;Fuut;Kajak;Onbekend;", "A/1/2;Meeuw;Kajak;Onbekend;")
    uitkomst = beoordeling(data, actor, {"2": str(anna.id), "3": "club", "4": "overslaan"})
    assert [(u.uitkomst, u.via) for u in uitkomst.values()] == [
        ("nieuwe boot", "keuze"), ("nieuwe boot", "keuze"), ("overgeslagen", "")]
    assert uitkomst[2].lid.id == anna.id and uitkomst[3].club


def test_koppelen_slaat_de_keuzes_op_en_vervangt_wat_er_stond(app, actor, anna):
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;X;", "A/1/2;Fuut;Kajak;Y;"), actor)
    bezetting_csv.koppelen({"2": str(anna.id), "3": "club"}, actor)
    assert db.session.scalar(select(Bezettingsimport)).keuzes == {"2": str(anna.id), "3": "club"}
    bezetting_csv.koppelen({"2": "", "3": "overslaan"}, actor)
    assert db.session.scalar(select(Bezettingsimport)).keuzes == {"3": "overslaan"}


@pytest.mark.parametrize("keuzes", [{"9": "club"}, {"2": "424242"}, {"2": "abc"}, {"2": "club", "3": "club"}],
                         ids=["regel", "lid", "tekst", "tweede-regel"])
def test_koppelen_weigert_een_onbekende_regel_of_lid_en_laat_de_oude_keuzes_staan(app, actor, anna, keuzes):
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;X;"), actor)
    bezetting_csv.koppelen({"2": "overslaan"}, actor)
    with pytest.raises(Regelfout, match="keuzes kloppen niet"):
        bezetting_csv.koppelen(keuzes, actor)
    assert db.session.scalar(select(Bezettingsimport)).keuzes == {"2": "overslaan"}


def test_koppelen_weigert_een_oud_lid_want_die_staat_niet_in_de_keuzelijst(app, actor):
    oud = lid("1002", "Oud Lid")
    eigenaar("UPDATE lid SET opzegdatum = '2020-01-01' WHERE id = :i", i=oud.id)
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;X;"), actor)
    with pytest.raises(Regelfout, match="keuzes kloppen niet"):
        bezetting_csv.koppelen({"2": str(oud.id)}, actor)
    assert db.session.scalar(select(Bezettingsimport)).keuzes == {}


# Bevestigen


def test_bevestigen_voert_elke_uitkomst_uit_met_het_log_van_de_bootmutaties(app, actor, anna):
    wachtend = boot(anna.id, "Kajak", "Fuut")
    wachtlijst.erop_zetten(wachtend.id, None, CLI)
    leg("A/1/1", "Reiger", anna.id)  # ongewijzigd
    plaats("A/1/2")  # toewijzen van Fuut, die van de wachtlijst gaat
    leg("A/1/3", "Meeuw", anna.id)  # overschrijven door Kievit
    kievit = boot(anna.id, "Kajak", "Kievit")
    _p, spreeuw = leg("A/1/4", "Spreeuw", anna.id)  # verplaatsen naar A/1/5
    plaats("A/1/5")
    plaats("A/1/6")  # nieuwe boot
    plaats("A/1/7")  # overgeslagen
    bezetting_csv.uploaden(bestand(
        "A/1/1;Reiger;Kajak;;1001", "A/1/2;Fuut;Kajak;;1001", "A/1/3;Kievit;Kajak;;1001",
        "A/1/5;Spreeuw;Kajak;;1001", "A/1/6;Nieuwkomer;Kajak;Anna de Vries;", "A/1/7;Overslaan;Kajak;;1001"),
        actor)
    bezetting_csv.koppelen({"7": "overslaan"}, actor)
    voor = len(acties())

    assert bezetting_csv.bevestigen(actor) == {
        "regels": 6, "nieuw": 1, "toegewezen": 1, "overschreven": 1, "verplaatst": 1,
        "ongewijzigd": 1, "overgeslagen": 1, "koppelingen": 0}
    db.session.expire_all()
    codes = {p.code: p.boot.naam if p.boot else None for r in indeling.rekken() for p in r.plaatsen}
    assert codes == {"A/1/1": "Reiger", "A/1/2": "Fuut", "A/1/3": "Kievit", "A/1/4": None,
                     "A/1/5": "Spreeuw", "A/1/6": "Nieuwkomer", "A/1/7": None}
    assert db.session.get(Boot, wachtend.id).wachtlijst is None
    assert db.session.get(Boot, kievit.id).plaats.code == "A/1/3"
    assert db.session.get(Boot, spreeuw.id).plaats.code == "A/1/5"
    assert db.session.scalar(select(Boot).where(Boot.naam == "Meeuw")) is not None  # blijft bestaan
    # Eerst de nieuwe boot, dan alle vrijgaven (A/1/3 en A/1/4), dan de toewijzingen op plaatsvolgorde.
    assert acties()[voor:] == [
        "boot.aangemaakt", "plaats.vrijgegeven", "plaats.vrijgegeven", "plaats.toegewezen",
        "wachtlijst.verwijderd", "plaats.toegewezen", "plaats.toegewezen", "plaats.toegewezen",
        "bezetting.geimporteerd"]
    assert db.session.scalar(select(Bezettingsimport)) is None


def test_bevestigen_logt_in_het_technische_log_alleen_aantallen_zonder_namen_uit_het_bestand(app, actor, anna):
    plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Geheimeboot;Kajak;Anna de Vries;1001"), actor)
    bezetting_csv.bevestigen(actor)
    [regel] = technisch()
    assert regel.verwijzingen == [] and regel.actor_id == actor.id
    assert regel.gegevens == {"regels": 1, "nieuw": 1, "toegewezen": 0, "overschreven": 0,
                              "verplaatst": 0, "ongewijzigd": 0, "overgeslagen": 0, "koppelingen": 0}
    assert "Geheimeboot" not in str(regel.gegevens) and "Anna" not in str(regel.gegevens)
    assert "bezetting.geimporteerd" in log.TECHNISCH and "bezetting.geimporteerd" not in log.BOOTMUTATIES
    assert [r.actie for r in log.regels(technisch=True, limiet=100) if r.actie.startswith("bezetting")] == [
        "bezetting.geimporteerd"]


def test_bevestigen_ruilt_twee_boten_van_plaats_in_een_transactie(app, actor, anna):
    """Eerst alle vrijgaven, dan alle toewijzingen, na een flush: de plaats van een boot is uniek."""
    _p1, een = leg("A/1/1", "Reiger", anna.id)
    _p2, twee = leg("A/1/2", "Fuut", anna.id)
    bezetting_csv.uploaden(bestand("A/1/1;Fuut;Kajak;;1001", "A/1/2;Reiger;Kajak;;1001"), actor)
    bezetting_csv.bevestigen(actor)
    db.session.expire_all()
    assert (db.session.get(Boot, een.id).plaats.code, db.session.get(Boot, twee.id).plaats.code) == (
        "A/1/2", "A/1/1")


def test_bevestigen_weigert_zolang_een_regel_te_koppelen_is_en_laat_alles_staan(app, actor, anna):
    plaats("A/1/1")
    plaats("A/1/2")
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;1001", "A/1/2;Fuut;Kajak;Onbekend;"), actor)
    voor = stand()
    with pytest.raises(Regelfout, match="regels te koppelen of met een fout"):
        bezetting_csv.bevestigen(actor)
    assert stand() == voor and db.session.scalar(select(Bezettingsimport)) is not None
    assert not technisch() and not bezetting_csv.overzicht()["kan_bevestigen"]


def test_bevestigen_controleert_elke_regel_opnieuw_als_de_stand_na_de_upload_veranderde(app, actor, anna):
    p = plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;1001"), actor)
    indeling.plaats_wijzigen(p.id, [soort("Surfski")], False, CLI)  # Kajak past niet meer
    voor = stand()
    with pytest.raises(Regelfout, match="regels te koppelen of met een fout"):
        bezetting_csv.bevestigen(actor)
    assert stand() == voor and not technisch()


def test_een_fout_bij_het_toewijzen_draait_alles_terug_ook_de_nieuwe_boten(app, actor, anna):
    plaats("A/1/1")
    plaats("A/1/2")
    bezetting_csv.uploaden(bestand("A/1/1;Eerste;Kajak;;1001", "A/1/2;Tweede;Kajak;;1001"), actor)
    voor = stand()
    echt = toewijzing._toewijzen
    aantal = []

    def faalt_bij_de_tweede(p, b, actor):
        aantal.append(b.naam)
        if len(aantal) == 2:
            raise RuntimeError("storing")
        return echt(p, b, actor)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(toewijzing, "_toewijzen", faalt_bij_de_tweede)
        with pytest.raises(RuntimeError):
            bezetting_csv.bevestigen(actor)
    assert aantal == ["Eerste", "Tweede"]
    assert stand() == voor and db.session.scalar(select(Bezettingsimport)) is not None


def test_bevestigen_geeft_een_melding_zonder_bestandsinhoud_als_het_toewijzen_toch_weigert(app, actor, anna):
    """De controle is net gedaan; weigert de kern toch, dan bevat de melding geen naam uit het bestand."""
    plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Geheimeboot;Kajak;;1001"), actor)

    def weigert(p, b, actor):
        raise Regelfout(f"Boot {b.naam} kan niet.")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(toewijzing, "_toewijzen", weigert)
        with pytest.raises(Regelfout) as fout:
            bezetting_csv.bevestigen(actor)
    assert "Geheimeboot" not in str(fout.value) and "niet uitgevoerd" in str(fout.value)
    assert db.session.scalar(select(Boot).where(Boot.naam == "Geheimeboot")) is None


def test_bevestigen_onthoudt_de_gekozen_koppeling_en_een_tweede_import_gebruikt_haar(app, actor, anna):
    plaats("A/1/1")
    plaats("A/1/2")
    plaats("C/1/1", club=True)
    beoordeling(bestand("A/1/1;Reiger;Kajak;Anna Vries;", "C/1/1;Clubkajak;Kajak;Clubkajakker;",
                        "A/1/2;Fuut;Kajak;Overslaan Man;"), actor,
                {"2": str(anna.id), "3": "club", "4": "overslaan"})
    assert bezetting_csv.bevestigen(actor)["koppelingen"] == 2
    ks = {k.naam: (k.lid_id, k.clubboot) for k in bezetting_csv.koppelingen()}
    assert ks == {"Anna Vries": (anna.id, False), "Clubkajakker": (None, True)}  # overslaan niet
    plaats("A/1/3")
    uitkomst = beoordeling(bestand("A/1/3;Meeuw;Kajak;Anna Vries;"), actor)
    assert (uitkomst[2].uitkomst, uitkomst[2].via, uitkomst[2].lid.id) == ("nieuwe boot", "koppeling", anna.id)


def test_een_gekozen_koppeling_vervangt_een_oudere_voor_dezelfde_naam_en_gebruik_vernieuwt_de_datum(app, actor, anna):
    bert = lid("1002", "Bert Jansen")
    plaats("A/1/1")
    plaats("A/1/2")
    db.session.add(Naamkoppeling(naam="Bertje", lid_id=bert.id, gebruikt_op=datetime(2020, 1, 1, tzinfo=UTC)))
    db.session.add(Naamkoppeling(naam="Annie", lid_id=anna.id, gebruikt_op=datetime(2020, 1, 1, tzinfo=UTC)))
    db.session.commit()
    beoordeling(bestand("A/1/1;Reiger;Kajak;Bertje;", "A/1/2;Fuut;Kajak;Annie;"), actor, {"2": str(anna.id)})
    assert bezetting_csv.bevestigen(actor)["koppelingen"] == 1
    db.session.expire_all()
    k = {k.naam: k for k in db.session.scalars(select(Naamkoppeling))}
    assert k["Bertje"].lid_id == anna.id  # de nieuwe keuze vervangt de oude
    assert all(k[n].gebruikt_op.year >= 2026 for n in ("Bertje", "Annie"))  # ook het gebruik telt


def test_koppeling_verwijderen_logt_een_verwijzing_zonder_naam_en_onbekend_is_een_melding(app, actor, anna):
    db.session.add_all([Naamkoppeling(naam="Annie", lid_id=anna.id), Naamkoppeling(naam="Club", clubboot=True)])
    db.session.commit()
    ids = {k.naam: k.id for k in bezetting_csv.koppelingen()}
    bezetting_csv.koppeling_verwijderen(ids["Annie"], actor)
    bezetting_csv.koppeling_verwijderen(ids["Club"], actor)
    regels = technisch("naamkoppeling.verwijderd")
    assert [(r.verwijzingen, r.gegevens, r.actor_id) for r in regels] == [
        ([f"lid:{anna.id}"], {}, actor.id), (["clubboot"], {}, actor.id)]
    assert "naamkoppeling.verwijderd" in log.TECHNISCH and not bezetting_csv.koppelingen()
    with pytest.raises(Regelfout, match="bestaat niet"):
        bezetting_csv.koppeling_verwijderen(ids["Annie"], actor)


def test_het_technische_log_van_een_mislukte_bevestiging_bevat_geen_bestandsinhoud(app, actor, anna, caplog):
    plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Geheimeboot;Kajak;Geheimlid;"), actor)
    with pytest.raises(Regelfout):
        bezetting_csv.bevestigen(actor)
    assert not technisch() and "Geheim" not in caplog.text


# Vergrendelen en races


def bevestig_in_thread(app, actor, anders):
    actie = alleen_regelfouten(lambda: bezetting_csv.bevestigen(actor), anders)

    def doe():
        with app.app_context():
            try:
                actie()
            except Regelfout:
                pass

    return threading.Thread(target=doe)


def wacht_op_slot(app, actor, vergrendel_sql, probe_sql, params):
    """De eerste verbinding houdt een slot (vergrendel_sql). bevestigen moet daarop wachten en
    houdt dan de eerdere sloten al vast: de probe (FOR UPDATE NOWAIT) mag die niet kunnen nemen."""
    anders, engine = [], create_engine(WEB)
    with engine.connect() as eerste, engine.connect() as probe:
        eerste.execute(text(vergrendel_sql), params)
        draad = bevestig_in_thread(app, actor, anders)
        draad.start()
        draad.join(timeout=1)
        assert draad.is_alive(), "bevestigen wacht niet op het slot"
        with pytest.raises(OperationalError, match="could not obtain lock"):
            probe.execute(text(probe_sql), params)
        eerste.commit()
        draad.join(timeout=10)
    engine.dispose()
    assert not draad.is_alive() and not anders
    db.session.expire_all()


def test_bevestigen_vergrendelt_eerst_de_boten_en_dan_de_plaatsen(app, actor, anna):
    """Een andere sessie houdt de plaats vast; bevestigen heeft dan de boot al vast, zoals toewijzen
    (boot, dan plaats). Zonder slot of met de plaats eerst kan de probe de boot wel nemen."""
    _p, b = leg("A/1/1", "Reiger", anna.id)
    q = plaats("A/1/2")
    bezetting_csv.uploaden(bestand("A/1/2;Reiger;Kajak;;1001"), actor)  # verplaatsen
    wacht_op_slot(app, actor, "SELECT id FROM plaats WHERE id = :q FOR UPDATE",
                  "SELECT id FROM boot WHERE id = :b FOR UPDATE NOWAIT", {"q": q.id, "b": b.id})
    assert db.session.get(Plaats, q.id).boot_id == b.id


def test_bevestigen_vergrendelt_de_boten_oplopend_op_id(app, actor, anna):
    plaats("A/1/1")
    plaats("A/1/2")
    laag = boot(anna.id, "Kajak", "Laag")
    hoog = boot(anna.id, "Kajak", "Hoog")
    assert laag.id < hoog.id
    bezetting_csv.uploaden(bestand("A/1/1;Hoog;Kajak;;1001", "A/1/2;Laag;Kajak;;1001"), actor)
    wacht_op_slot(app, actor, "SELECT id FROM boot WHERE id = :hoog FOR UPDATE",
                  "SELECT id FROM boot WHERE id = :laag FOR UPDATE NOWAIT",
                  {"hoog": hoog.id, "laag": laag.id})


def test_bevestigen_vergrendelt_de_plaatsen_oplopend_op_id(app, actor, anna):
    laag, hoog = plaats("A/1/1"), plaats("A/1/2")
    assert laag.id < hoog.id
    bezetting_csv.uploaden(bestand("A/1/2;Eerste;Kajak;;1001", "A/1/1;Tweede;Kajak;;1001"), actor)
    wacht_op_slot(app, actor, "SELECT id FROM plaats WHERE id = :hoog FOR UPDATE",
                  "SELECT id FROM plaats WHERE id = :laag FOR UPDATE NOWAIT",
                  {"hoog": hoog.id, "laag": laag.id})


def test_twee_beheerders_bevestigen_niet_tegelijk_de_tweede_wacht_op_de_lopende_import(app, actor, anna):
    plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;1001"), actor)
    anders = []
    fouten = race(app, ["SELECT id FROM bezettingsimport FOR UPDATE",
                        "DELETE FROM bezettingsimport"], {},
                  alleen_regelfouten(lambda: bezetting_csv.bevestigen(actor), anders))
    assert fouten == ["Er loopt geen bezettingsimport, of die is verlopen. Upload het bestand opnieuw."]
    assert not anders and not technisch()


@pytest.mark.parametrize("wat", ["koppelen", "annuleren"])
def test_koppelen_en_annuleren_wachten_op_een_lopende_bevestiging(app, actor, anna, wat):
    """De eerste sessie bevestigt (verwijdert de import); de tweede ziet daarna geen import."""
    plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;1001"), actor)
    actie = {"koppelen": lambda: bezetting_csv.koppelen({"2": "overslaan"}, actor),
             "annuleren": lambda: bezetting_csv.annuleren(actor)}[wat]
    fouten = race(app, ["SELECT id FROM bezettingsimport FOR UPDATE",
                        "DELETE FROM bezettingsimport"], {}, actie)
    assert fouten == ["Er loopt geen bezettingsimport, of die is verlopen. Upload het bestand opnieuw."]


def test_een_boot_of_plaats_die_intussen_verandert_wordt_na_het_vergrendelen_opnieuw_beoordeeld(app, actor, anna):
    """Tussen de eerste beoordeling en het slot legt een andere beheerder een boot op de plaats.
    De regel is dan een overschrijving van een boot die we niet vergrendelden: niets gebeurt."""
    p = plaats("A/1/1")
    gast = boot(anna.id, "Kajak", "Gast")
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;1001"), actor)
    anders = []
    fouten = race(app, ["SELECT id FROM plaats WHERE id = :p FOR UPDATE",
                        "UPDATE plaats SET boot_id = :g WHERE id = :p"], {"p": p.id, "g": gast.id},
                  alleen_regelfouten(lambda: bezetting_csv.bevestigen(actor), anders))
    assert fouten == ["Er is intussen iets veranderd aan de boten of plaatsen. Probeer het opnieuw."]
    assert not anders
    db.session.expire_all()
    assert db.session.get(Plaats, p.id).boot_id == gast.id
    assert db.session.scalar(select(Boot).where(Boot.naam == "Reiger")) is None
    assert db.session.scalar(select(Bezettingsimport)) is not None


def test_een_plaats_die_intussen_clubplaats_wordt_geeft_de_algemene_melding_van_de_tweede_controle(app, actor, anna):
    p = plaats("A/1/1")
    bezetting_csv.uploaden(bestand("A/1/1;Reiger;Kajak;;1001"), actor)
    fouten = race(app, ["SELECT id FROM plaats WHERE id = :p FOR UPDATE",
                        "UPDATE plaats SET is_clubplaats = true WHERE id = :p"], {"p": p.id},
                  lambda: bezetting_csv.bevestigen(actor))
    assert len(fouten) == 1 and "regels te koppelen of met een fout" in fouten[0]
    assert db.session.scalar(select(Boot).where(Boot.naam == "Reiger")) is None
