"""Rekindeling exporteren en importeren als CSV (issue #157, ADR-014 §1 en §2): formaat, lege
export als sjabloon, rondgang, elke validatieregel, alles of niets en de webroutes."""

import io
import re
import time

import pytest
from sqlalchemy import select

from app.domein import CLI, Regelfout, csvbestand, indeling, rekindeling_csv, toewijzing
from app.domein.csvbestand import CsvFout
from app.models import Bootsoort, Logregel, Plaats, Rek, db
from tests.unit.hulp import lid, race
from tests.unit.test_indeling_en_toewijzing import acties, boot, plaats, soort
from tests.unit.test_web_beheer import ingelogd  # noqa: F401  fixture

KOP = "rek;omschrijving;verdieping;vak;bootsoorten;clubplaats"


def bestand(*regels, kop=KOP, bom=True):
    """Een CSV-bestand als bytes, standaard UTF-8 met BOM zoals de export."""
    tekst = "\r\n".join([kop, *regels]) + "\r\n"
    return (("﻿" if bom else "") + tekst).encode("utf-8")


def importeer(data):
    return rekindeling_csv.importeren(data, CLI)


def fouten_van(data):
    with pytest.raises(CsvFout) as fout:
        importeer(data)
    return fout.value.regels


def stand():
    """Alles wat een import mag wijzigen, met de ids: een rondgang laat dit gelijk."""
    db.session.expire_all()
    reks = [(r.id, r.naam, r.omschrijving, r.volgorde) for r in db.session.scalars(
        select(Rek).order_by(Rek.id))]
    plaatsen = [(p.id, p.rek_id, p.verdieping, p.vak, p.publieke_sleutel, p.is_clubplaats,
                 p.boot_id, [s.id for s in p.bootsoorten]) for p in db.session.scalars(
        select(Plaats).order_by(Plaats.id))]
    return reks, plaatsen, len(acties())


def lijn(data, i):
    return data.decode("utf-8-sig").splitlines()[i]


# Export


def test_export_zonder_rekken_is_bom_en_kopregel(app):
    assert rekindeling_csv.export() == b"\xef\xbb\xbf" + KOP.encode() + b"\r\n"


def test_export_een_regel_per_plaats_in_de_volgorde_van_de_loods(app):
    plaats("B/1/1", ("Kajak",))  # B is het eerste rek, A het tweede
    plaats("A/1/1", ("Kajak", "Surfski"), club=True)
    plaats("A/2/1", ("C11",))
    indeling.rek_wijzigen(db.session.scalar(select(Rek).where(Rek.naam == "A")).id, "A",
                          "Links; \"voor\"", CLI)
    tekst = rekindeling_csv.export().decode("utf-8-sig")
    assert tekst.split("\r\n")[:-1] == [
        KOP, "B;;1;1;Kajak;nee", 'A;"Links; ""voor""";1;1;Kajak/Surfski;ja', 'A;"Links; ""voor""";2;1;C11;nee']


def test_export_neutraliseert_een_formule_en_de_import_zet_haar_terug(app):
    omschrijvingen = ["=1+1", "+1", "-1", "@x", "'=x", "'x", "gewoon"]
    for i, tekst in enumerate(omschrijvingen):
        plaats(f"R{i}/1/1", ("Kajak",))
        indeling.rek_wijzigen(db.session.scalar(select(Rek).where(Rek.naam == f"R{i}")).id,
                              f"R{i}", tekst, CLI)
    data = rekindeling_csv.export()
    cellen = [lijn(data, i + 1).split(";")[1] for i in range(len(omschrijvingen))]
    assert cellen == ["'=1+1", "'+1", "'-1", "'@x", "''=x", "'x", "gewoon"]
    voor = stand()
    importeer(data)
    assert stand() == voor
    assert [r.omschrijving for r in db.session.scalars(select(Rek).order_by(Rek.id))] == omschrijvingen


def test_export_weigert_een_bootsoort_met_een_schuine_streep(app):
    plaats()
    db.session.add(Bootsoort(naam="Zee/kajak"))
    db.session.commit()
    with pytest.raises(Regelfout, match="Zee/kajak bevat een /"):
        rekindeling_csv.export()
    with pytest.raises(Regelfout, match="Zee/kajak bevat een /"):
        rekindeling_csv.export(leeg=True)


def test_export_weigert_een_rek_dat_met_hekje_begint(app):
    db.session.add(Rek(naam="#oud"))
    db.session.commit()
    with pytest.raises(Regelfout, match="#oud begint met #"):
        rekindeling_csv.export()


def test_hekje_en_schuine_streep_zijn_geen_naam_van_een_rek_of_soort(app):
    for naam in ("#A", "A/B"):
        with pytest.raises(Regelfout, match="zonder / en zonder # vooraan"):
            indeling.rek_aanmaken(naam, "", {(1, 1)}, CLI)
    plaats("C/1/1")
    with pytest.raises(Regelfout, match="zonder / en zonder # vooraan"):
        indeling.rek_wijzigen(db.session.scalar(select(Rek)).id, "#C", "", CLI)
    with pytest.raises(Regelfout, match="zonder /"):
        indeling.bootsoort_toevoegen("Zee/kajak", CLI)
    with pytest.raises(Regelfout, match="zonder /"):
        indeling.bootsoort_hernoemen(soort("Kajak"), "Zee/kajak", CLI)


# Lege export als sjabloon


def test_lege_export_is_een_sjabloon_met_uitleg_en_verandert_niets(app):
    data = rekindeling_csv.export(leeg=True)
    regels = data.decode("utf-8-sig").splitlines()
    assert data.startswith(b"\xef\xbb\xbf") and regels[-1] == KOP
    assert all(r.startswith("#") for r in regels[:-1])
    tekst = "\n".join(regels)
    assert "Kajak, Canadese kano, Surfski, C11, Supboard" in tekst
    assert "# Voorbeeld: A;Stelling links;1;1;Kajak/Canadese kano;nee" in regels
    assert "gescheiden door /" in tekst and "ja of nee" in tekst
    plaats()
    voor = stand()
    assert importeer(data) == dict.fromkeys(
        ("rekken_nieuw", "rekken_gewijzigd", "plaatsen_nieuw", "plaatsen_gewijzigd"), 0)
    assert stand() == voor


def test_rondgang_met_een_plaats_zonder_bootsoort(app):
    rek = indeling.rek_aanmaken("A", "", {(1, 1), (1, 2)}, CLI)
    indeling.plaats_wijzigen(rek.plaatsen[0].id, [soort("Kajak")], False, CLI)
    data = rekindeling_csv.export()
    assert lijn(data, 2) == "A;;1;2;;nee"
    voor = stand()
    importeer(data)
    assert stand() == voor
    # Een lege cel haalt de bootsoort van een bestaande plaats niet weg, zoals op het scherm.
    regels = fouten_van(bestand("A;;1;1;;nee"))
    assert regels == ["Regel 2: Kies minstens één bootsoort die op de plaats past."]
    assert stand() == voor
    # Een nieuwe plaats mag leeg zijn.
    assert importeer(bestand("A;;1;3;;nee"))["plaatsen_nieuw"] == 1


def test_lege_bootsoorten_op_een_bezette_plaats_wordt_geweigerd(app):
    p = plaats("A/1/1", ("Kajak",))
    toewijzing.toewijzen(p.id, boot(lid().id).id, CLI)
    voor = stand()
    regels = fouten_van(bestand("A;;1;1;;nee"))
    assert regels == ["Regel 2: Kies minstens één bootsoort die op de plaats past."]
    assert stand() == voor


def test_stuurteken_in_naam_of_omschrijving_wordt_niet_opgeslagen(app):
    for naam, omschrijving in (("A\x07", ""), ("A", "a\tb"), ("A", "a\x00b"), ("A", "a\x1fb")):
        with pytest.raises(Regelfout, match="stuurtekens"):
            indeling.rek_aanmaken(naam, omschrijving, {(1, 1)}, CLI)
    rek = indeling.rek_aanmaken("A", "", {(1, 1)}, CLI)
    with pytest.raises(Regelfout, match="stuurtekens"):
        indeling.rek_wijzigen(rek.id, "A", "a\nb", CLI)


def test_stuurteken_in_een_bootsoortnaam_wordt_niet_opgeslagen(app):
    for naam in ("Zee\x07kajak", "Zee\tkajak"):
        with pytest.raises(Regelfout, match="stuurtekens"):
            indeling.bootsoort_toevoegen(naam, CLI)
    with pytest.raises(Regelfout, match="stuurtekens"):
        indeling.bootsoort_hernoemen(soort("Kajak"), "Ka\x00jak", CLI)


def test_het_voorbeeld_uit_de_lege_export_is_een_geldige_regel(app):
    data = rekindeling_csv.export(leeg=True).decode("utf-8-sig")
    voorbeeld = next(r for r in data.splitlines() if r.startswith("# Voorbeeld")).replace(
        "# Voorbeeld: ", "")
    assert importeer(bestand(voorbeeld)) == {"rekken_nieuw": 1, "rekken_gewijzigd": 0,
                                             "plaatsen_nieuw": 1, "plaatsen_gewijzigd": 0}


# Rondgang


def test_rondgang_van_een_export_verandert_niets(app):
    vrij = plaats("A/1/1", ("Kajak", "Surfski"))
    bezet = plaats("A/1/2", ("Kajak",))
    plaats("A/2/1", ("C11",), club=True)
    plaats("tweede/1/1", ("Canadese kano",))
    toewijzing.toewijzen(bezet.id, boot(lid().id).id, CLI)
    indeling.rek_wijzigen(vrij.rek_id, "A", "Links, bij de deur", CLI)
    voor = stand()
    assert importeer(rekindeling_csv.export()) == dict.fromkeys(
        ("rekken_nieuw", "rekken_gewijzigd", "plaatsen_nieuw", "plaatsen_gewijzigd"), 0)
    assert stand() == voor


def test_import_bouwt_een_lege_installatie_op_uit_een_export(app):
    plaats("A/1/1", ("Kajak", "Surfski"))
    plaats("A/2/1", ("C11",), club=True)
    data = rekindeling_csv.export()
    for r in db.session.scalars(select(Rek)):
        indeling.rek_verwijderen(r.id, CLI)
    assert importeer(data)["plaatsen_nieuw"] == 2
    assert rekindeling_csv.export() == data


# Importeren: aanmaken en bijwerken


def test_import_maakt_aan_en_werkt_bij_en_laat_de_rest_staan(app):
    bezet = plaats("A/1/1", ("Kajak", "Surfski"))
    plaats("A/1/2", ("Kajak",))
    plaats("A/1/3", ("Kajak",))  # niet in het bestand: blijft
    toewijzing.toewijzen(bezet.id, boot(lid().id).id, CLI)
    n = importeer(bestand(
        "A;Nieuwe omschrijving;1;1;Kajak/Surfski/C11;nee",   # bezet, nog geschikt: soorten erbij
        "a;Nieuwe omschrijving;1;2;C11;ja",                   # hoofdletter anders: zelfde rek
        "A;Nieuwe omschrijving;1;4;Kajak;nee",                # nieuwe plaats in bestaand rek
        "Nieuw;;1;1;Supboard;nee",                            # nieuw rek
        "Nieuw;;1;2;kajak/SURFSKI;ja"))                       # soortnamen zonder hoofdletters
    assert n == {"rekken_nieuw": 1, "rekken_gewijzigd": 1, "plaatsen_nieuw": 3,
                 "plaatsen_gewijzigd": 2}
    db.session.expire_all()
    codes = {p.code: ([s.naam for s in p.bootsoorten], p.is_clubplaats, p.boot_id is not None)
             for p in db.session.scalars(select(Plaats))}
    assert codes == {
        "A/1/1": (["Kajak", "Surfski", "C11"], False, True),
        "A/1/2": (["C11"], True, False),
        "A/1/3": (["Kajak"], False, False),
        "A/1/4": (["Kajak"], False, False),
        "Nieuw/1/1": (["Supboard"], False, False),
        "Nieuw/1/2": (["Kajak", "Surfski"], True, False)}
    rek_a, rek_nieuw = (db.session.scalar(select(Rek).where(Rek.naam == n)) for n in ("A", "Nieuw"))
    assert rek_a.omschrijving == "Nieuwe omschrijving" and rek_a.naam == "A"
    assert rek_nieuw.volgorde > rek_a.volgorde


def test_import_schrijft_alleen_aantallen_in_het_technische_log(app):
    plaats("A/1/1")
    importeer(bestand("Geheimrek;Een omschrijving;1;1;Kajak;nee"))
    regel = db.session.scalars(select(Logregel).where(Logregel.actie == "indeling.geimporteerd")
                               ).one()
    assert regel.gegevens == {"rekken_nieuw": 1, "rekken_gewijzigd": 0, "plaatsen_nieuw": 1,
                              "plaatsen_gewijzigd": 0}
    assert "Geheimrek" not in str(regel.gegevens) + str(regel.verwijzingen)
    assert regel.actor_naam == "cli"
    assert acties().count("rek.aangemaakt") == 2 and acties().count("plaats.aangemaakt") == 2


def test_import_zonder_regels_verandert_niets_en_logt_niets(app):
    plaats()
    voor = stand()
    importeer(bestand())
    importeer(bestand(";;;;;", "# commentaar"))
    assert stand() == voor


@pytest.mark.parametrize("data", [
    bestand("A;;1;1;Kajak;nee", bom=False),
    bestand("A;;1;1;Kajak;nee"),
    bestand("A;;1;1;Kajak;nee").replace(b"\r\n", b"\n"),
    bestand("# eerst commentaar", "", "A;;1;1;Kajak;nee", ";;;;;"),
    bestand('"# ook gequote commentaar";x', "A;;1;1;Kajak;nee"),
    bestand("A;;1;1;Kajak;nee", kop="Clubplaats;BOOTSOORTEN;Vak;Verdieping;Omschrijving;Rek"
            ).replace(b"A;;1;1;Kajak;nee", b"nee;Kajak;1;1;;A"),
], ids=["zonder BOM", "met BOM", "LF", "commentaar en lege regels", "gequote commentaar",
        "kolomvolgorde vrij"])
def test_import_leest_wat_excel_schrijft(app, data):
    assert importeer(data)["plaatsen_nieuw"] == 1
    assert [p.code for p in db.session.scalars(select(Plaats))] == ["A/1/1"]


# Importeren: bestandsregels (ADR-014 §1)


def test_te_groot_bestand_weigert_en_precies_de_grens_niet(app):
    kop = (KOP + "\r\n").encode()
    exact = kop + ("#" + "x" * 1000 + "\r\n").encode() * 200
    exact += b"#" + b"x" * (csvbestand.MAX_BYTES - len(exact) - 1)
    assert len(exact) == csvbestand.MAX_BYTES
    assert importeer(exact)["plaatsen_nieuw"] == 0
    assert fouten_van(exact + b"x") == ["Het bestand is groter dan 256 kB."]


def test_te_veel_regels_weigert_en_precies_de_grens_niet(app):
    genoeg = bestand(*["# c"] * (csvbestand.MAX_REGELS - 1))
    assert len(genoeg.decode().splitlines()) == csvbestand.MAX_REGELS
    importeer(genoeg)
    assert fouten_van(genoeg + b"# c\r\n") == ["Het bestand heeft meer dan 2000 regels."]


@pytest.mark.parametrize("data, melding", [
    (b"rek,omschrijving,verdieping,vak,bootsoorten,clubplaats\r\nA,,1,1,Kajak,nee\r\n",
     "geen puntkomma"),
    (KOP.replace(";", "\t").encode() + b"\r\n", "geen puntkomma"),
    ("rek;omschrijving;verdieping;vak;bootsoorten;clubplaats\r\nA;\xe9;1;1;Kajak;nee".encode(
        "cp1252"), "geen UTF-8"),
    (KOP.encode("utf-16"), "geen CSV-bestand"),
    (b"PK\x03\x04\x00\x00" + KOP.encode(), "geen CSV-bestand"),
    (b"", "geen kopregel"),
    (b"# alleen commentaar\r\n", "geen kopregel"),
    ((KOP + "\r\n").replace("clubplaats", "kleur").encode(),
     "kolom ontbreekt: clubplaats; onbekende kolom: kleur"),
    ((KOP + ";extra\r\n").encode(), "onbekende kolom: extra"),
    ((KOP + ";rek\r\n").encode(), "twee keer"),
    (bestand('A;"niet dicht;1;1;Kajak;nee'), "aanhalingstekens"),
], ids=["komma", "tab", "windows-1252", "utf-16", "xlsx", "leeg", "alleen commentaar",
        "kolom ontbreekt", "kolom erbij", "kolom dubbel", "aanhalingstekens"])
def test_bestand_dat_geen_geldige_csv_is_wordt_geweigerd(app, data, melding):
    plaats()
    voor = stand()
    regels = fouten_van(data)
    assert len(regels) == 1 and melding in regels[0]
    assert stand() == voor


def test_nul_en_stuurtekens_en_regeleinden_in_een_veld_zijn_een_fout(app):
    regels = fouten_van(bestand(
        "A;a\x07b;1;1;Kajak;nee",
        'A;"twee\r\nregels";1;2;Kajak;nee',
        "A;tab\there;1;3;Kajak;nee",
        "A;;1;4;Kajak"))
    # Een veld met regeleinde telt vanaf de regel waar het begint (regel 3 en 4).
    assert [r.split(":")[0] for r in regels] == ["Regel 2", "Regel 3", "Regel 5", "Regel 6"]
    assert all("stuurteken" in r for r in regels[:3]) and "6 kolommen verwacht, 5" in regels[3]


# Importeren: validatie per regel (ADR-014 §2)


@pytest.mark.parametrize("regel, melding", [
    ("A;;0;1;Kajak;nee", "verdieping moet een getal van 1 tot en met 5"),
    ("A;;6;1;Kajak;nee", "verdieping moet een getal van 1 tot en met 5"),
    ("A;;x;1;Kajak;nee", "verdieping moet een getal"),
    ("A;;1;13;Kajak;nee", "vak moet een getal van 1 tot en met 12"),
    ("A;;1;-1;Kajak;nee", "vak moet een getal"),
    ("A;;1;١;Kajak;nee", "vak moet een getal"),
    (f"{'A' * 11};;1;1;Kajak;nee", "naam van 1 tot 10 tekens"),
    (";;1;1;Kajak;nee", "naam van 1 tot 10 tekens"),
    ("A/B;;1;1;Kajak;nee", "zonder / en zonder # vooraan"),
    (f"A;{'x' * 61};1;1;Kajak;nee", "omschrijving heeft hooguit 60 tekens"),
    ("A;;1;1;Kajak;misschien", "clubplaats moet ja of nee zijn"),
    ("A;;1;1;Kajak//Surfski;nee", "bootsoorten mist een naam"),
    ("A;;1;1;Kajak/;nee", "bootsoorten mist een naam"),
    ("A;;1;1;Zeilboot;nee", "de bootsoort Zeilboot bestaat niet"),
    ("A;;1;1;Kajak/Zeilboot;nee", "de bootsoort Zeilboot bestaat niet"),
    (f"A;;1;1;{'Z' * 80};nee", f"de bootsoort {'Z' * 30}… bestaat niet"),
])
def test_foute_regel_weigert_het_hele_bestand_met_regelnummer_en_reden(app, regel, melding):
    plaats("Z/1/1")
    voor = stand()
    regels = fouten_van(bestand("Goed;;1;1;Kajak;nee", regel))
    assert len(regels) == 1 and regels[0].startswith("Regel 3: ") and melding in regels[0]
    assert stand() == voor  # ook het goede rek Goed is niet aangemaakt


def test_rek_met_hekje_in_een_andere_kolom_dan_de_eerste_is_een_fout(app):
    regels = fouten_van(bestand("nee;Kajak;1;1;;#A", kop="clubplaats;bootsoorten;verdieping;vak;"
                                                       "omschrijving;rek"))
    assert regels == [("Regel 2: Geef het rek een naam van 1 tot 10 tekens, zonder / en zonder # "
                       "vooraan en zonder stuurtekens.")]


def test_dubbele_plaats_en_afwijkende_omschrijving(app):
    regels = fouten_van(bestand("A;links;1;1;Kajak;nee", "a;links;1;1;Kajak;nee",
                                "A;rechts;1;2;Kajak;nee"))
    assert regels == ["Regel 3: plaats a/1/1 staat al op regel 2.",
                      "Regel 4: de omschrijving van rek A wijkt af van regel 2."]


def test_gat_in_een_verdieping_in_een_nieuw_rek_en_samen_met_bestaande_plaatsen(app):
    plaats("A/1/1")
    voor = stand()
    regels = fouten_van(bestand("Nieuw;;1;1;Kajak;nee", "Nieuw;;1;3;Kajak;nee",
                                "A;;1;3;Kajak;nee"))
    assert len(regels) == 2
    assert regels[0].startswith("Regel 2: rek Nieuw: Verdieping 1 heeft een gat: vak 2 ontbreekt")
    assert regels[1].startswith("Regel 4: rek A: Verdieping 1 heeft een gat: vak 2 ontbreekt")
    assert stand() == voor
    # Een gat dat de bestaande plaatsen vullen is geen gat.
    plaats("A/1/2")
    assert importeer(bestand("A;;1;3;Kajak;nee"))["plaatsen_nieuw"] == 1


@pytest.mark.parametrize("regel, melding", [
    ("A;;1;1;Surfski;nee", "Op plaats A/1/1 ligt Zeemeeuw, een kajak"),
    ("A;;1;1;Kajak;ja", "Geef de plaats eerst vrij voordat je de clubplaats wijzigt"),
], ids=["bootsoort", "clubplaats"])
def test_bezette_plaats_ongeschikt_of_clubplaats_maken_wordt_geweigerd(app, regel, melding):
    p = plaats("A/1/1", ("Kajak",))
    toewijzing.toewijzen(p.id, boot(lid().id).id, CLI)
    voor = stand()
    regels = fouten_van(bestand("Nieuw;;1;1;Kajak;nee", regel))
    assert len(regels) == 1 and regels[0].startswith("Regel 3: ") and melding in regels[0]
    assert stand() == voor


def test_bezette_clubplaats_blijft_een_clubplaats_en_de_soort_mag_erbij_komen(app):
    p = plaats("A/1/1", ("Kajak",), club=True)
    toewijzing.toewijzen(p.id, boot(None).id, CLI)
    assert importeer(bestand("A;;1;1;Kajak/Surfski;ja"))["plaatsen_gewijzigd"] == 1


def test_foute_regels_komen_samen_in_een_melding_op_volgorde_van_het_bestand(app):
    # Eerst de opbouw van elke regel, daarna wat de database erbij zegt.
    regels = fouten_van(bestand("A;;9;1;Kajak;nee", "B;;1;1;Zeilboot;nee", "C;;1;1;Kajak;ja/nee"))
    assert [r.split(":")[0] for r in regels] == ["Regel 2", "Regel 4"]
    regels = fouten_van(bestand("N;;1;1;Kajak;nee", "N;;1;3;Zeilboot;nee", "M;;1;1;Kajak;nee",
                                "M;;1;2;Kajak/Boot;nee"))
    assert [r.split(":")[0] for r in regels] == ["Regel 2", "Regel 3", "Regel 5"]
    assert "gat" in regels[0] and "Zeilboot" in regels[1] and "Boot" in regels[2]


def test_meer_dan_vijftig_meldingen_worden_afgekapt_met_het_aantal(app):
    regels = fouten_van(bestand(*["A;;1;1;Kajak;ja/nee"] * 60))
    assert len(regels) == csvbestand.MAX_MELDINGEN + 1
    assert regels[-1] == "En nog 10 meldingen."


def test_twee_soorten_die_alleen_in_hoofdletters_verschillen_zijn_dubbelzinnig(app):
    db.session.add(Bootsoort(naam="KAJAK"))
    db.session.commit()
    assert "dubbelzinnig" in fouten_van(bestand("A;;1;1;kajak;nee"))[0]
    # Precies zoals in de applicatie is wel eenduidig.
    assert importeer(bestand("A;;1;1;Kajak;nee", "A;;1;2;KAJAK;nee"))["plaatsen_nieuw"] == 2


# Gelijktijdig: de import vergrendelt eerst de rekken en plaatsen (ADR-014 §2). Zonder die
# vergrendeling ziet hij een plaats zonder boot en maakt hij haar ongeschikt voor die boot.


def test_gelijktijdig_toewijzen_en_import(app):
    p = plaats("A/1/1", ("Kajak", "Surfski"))
    b = boot(lid().id)
    fouten = race(app, ["SELECT id FROM plaats WHERE id = :p FOR UPDATE",
                        "UPDATE plaats SET boot_id = :b WHERE id = :p"], {"p": p.id, "b": b.id},
                  lambda: importeer(bestand("A;;1;1;Surfski;nee")))
    assert len(fouten) == 1 and "Regel 2: Op plaats A/1/1 ligt Zeemeeuw" in fouten[0]
    assert [s.naam for s in db.session.get(Plaats, p.id).bootsoorten] == ["Kajak", "Surfski"]


# Webroutes


def uploaden(client, data, naam="indeling.csv", **extra):
    return client.post("/rekindeling/import", data={"bestand": (io.BytesIO(data), naam)},
                       content_type="multipart/form-data", **extra)


def test_web_export_en_sjabloon(ingelogd):  # noqa: F811
    plaats("A/1/1", ("Kajak",))
    r = ingelogd.get("/rekindeling.csv")
    assert r.status_code == 200 and r.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert r.headers["Content-Disposition"] == 'attachment; filename="rekindeling.csv"'
    assert r.data == rekindeling_csv.export()
    r = ingelogd.get("/rekindeling.csv?leeg=1")
    assert r.headers["Content-Disposition"] == 'attachment; filename="rekindeling-leeg.csv"'
    assert r.data == rekindeling_csv.export(leeg=True) and b"# Voorbeeld" in r.data


def test_web_export_geeft_de_weigering_als_melding(ingelogd):  # noqa: F811
    db.session.add(Bootsoort(naam="Zee/kajak"))
    db.session.commit()
    r = ingelogd.get("/rekindeling.csv", follow_redirects=True)
    assert "Zee/kajak bevat een /" in r.text and r.request.path == "/import-export"


@pytest.mark.parametrize("methode, pad", [("get", "/rekindeling.csv"), ("post", "/rekindeling/import")])
def test_web_vraagt_inloggen(client, methode, pad):
    r = getattr(client, methode)(pad)
    assert r.status_code == 302 and r.location.endswith("/inloggen")


def test_web_import_vraagt_een_recente_inlog(ingelogd):  # noqa: F811
    with ingelogd.session_transaction() as s:
        s["ingelogd_op"] = int(time.time()) - 601
    r = uploaden(ingelogd, bestand("A;;1;1;Kajak;nee"))
    assert r.status_code == 302 and r.location.endswith("/inloggen")
    assert db.session.scalar(select(Rek)) is None


def test_web_import_vraagt_een_csrf_token(app, ingelogd):  # noqa: F811
    app.config["WTF_CSRF_ENABLED"] = True  # zoals in productie
    token = re.search(r'name="csrf-token" content="([^"]+)"', ingelogd.get("/import-export").text)[1]
    r = uploaden(ingelogd, bestand("A;;1;1;Kajak;nee"))
    assert r.status_code == 400 and db.session.scalar(select(Rek)) is None
    r = uploaden(ingelogd, bestand("A;;1;1;Kajak;nee"), headers={"X-CSRFToken": token})
    assert r.status_code == 302 and db.session.scalar(select(Rek)).naam == "A"


def test_web_import_meldt_het_resultaat_en_toont_het_in_de_indeling(ingelogd):  # noqa: F811
    r = uploaden(ingelogd, bestand("A;Links;1;1;Kajak;nee", "A;Links;1;2;Kajak;ja"),
                 follow_redirects=True)
    assert ("De indeling is geïmporteerd. Rekken: 1 nieuw, 0 gewijzigd. "
            "Plaatsen: 2 nieuw, 0 gewijzigd.") in r.text
    assert r.request.path == "/import-export"
    tekst = ingelogd.get("/indeling").text
    assert ">A/1/2</a>" in tekst and "Links" in tekst
    assert "rek.aangemaakt" not in r.text and "indeling.geimporteerd" in ingelogd.get(
        "/log/techniek").text


def test_web_import_toont_per_foute_regel_het_regelnummer_en_de_reden_geescaped(ingelogd):  # noqa: F811
    r = uploaden(ingelogd, bestand("A;;1;1;Kajak;nee", "A;;1;2;Kajak;vielleicht"))
    assert r.status_code == 422
    assert "<h1>Import/export</h1>" in r.text and "<h1>Indeling</h1>" not in r.text
    assert re.findall(r'aria-current="page">([^<]+)</a>', r.text) == ["Import/export"]
    assert re.search(r'<div class="ds-notice ds-notice--danger melding">.*?role="alert">\s*<p>Het bestand is niet geïmporteerd', r.text, re.DOTALL)
    assert "Het bestand is niet geïmporteerd. Er is niets veranderd." in r.text
    assert "<li>Regel 3: clubplaats moet ja of nee zijn.</li>" in r.text
    r = uploaden(ingelogd, bestand("A;;1;1;<b>x;nee"))  # zonder /, dat scheidt de soorten
    assert "<li>Regel 2: de bootsoort &lt;b&gt;x bestaat niet.</li>" in r.text
    assert "<b>x" not in r.text and db.session.scalar(select(Rek)) is None


@pytest.mark.parametrize("data, naam, melding", [
    (None, "", "Kies een CSV-bestand."),
    (bestand("A;;1;1;Kajak;nee"), "indeling.xlsx", "extensie .csv"),
    (bestand("A;;1;1;Kajak;nee"), "indeling.txt", "extensie .csv"),
])
def test_web_import_zonder_of_met_een_ander_bestandstype(ingelogd, data, naam, melding):  # noqa: F811
    r = ingelogd.post("/rekindeling/import", data={"bestand": (io.BytesIO(data or b""), naam)},
                      content_type="multipart/form-data", follow_redirects=True)
    assert melding in r.text and db.session.scalar(select(Rek)) is None


def test_web_import_leest_niet_verder_dan_de_grens(ingelogd):  # noqa: F811
    r = uploaden(ingelogd, bestand("A;;1;1;Kajak;nee") + b"#" + b"x" * csvbestand.MAX_BYTES)
    assert r.status_code == 422 and "groter dan 256 kB" in r.text
    assert db.session.scalar(select(Rek)) is None


def test_import_export_toont_de_knoppen_en_het_formulier(ingelogd):  # noqa: F811
    tekst = ingelogd.get("/import-export").text
    assert 'href="/rekindeling.csv"' in tekst and 'href="/rekindeling.csv?leeg=1"' in tekst
    assert 'action="/rekindeling/import"' in tekst and 'enctype="multipart/form-data"' in tekst
    assert 'name="bestand"' in tekst and 'name="csrf_token"' in tekst
    assert "hooguit 256 kB" in tekst and " style=" not in tekst and "<script" not in tekst
