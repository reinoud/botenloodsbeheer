"""Indeling met rek, verdieping en vak (issue #80, BLB-001, BLB-044, ADR-003 v2.1.0): grenzen,
uitzetten met en zonder boot, gaten, reknaam en omschrijving, volgorde, logregels en de races van
indeling_instellen."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DataError, IntegrityError

from app.domein import CLI, Regelfout, indeling, toewijzing, uitlezen
from app.models import Logregel, Plaats, Rek, db
from tests.unit.hulp import lid, race
from tests.unit.test_indeling_en_toewijzing import acties, boot


def rek(naam="A", vakken=((1, 1), (1, 2)), omschrijving=""):
    return indeling.rek_aanmaken(naam, omschrijving, set(vakken), CLI)


def codes(r):
    return [p.code for p in indeling.rek(r.id).plaatsen]


def aantal(model):
    return len(db.session.scalars(select(model)).all())


# Grenzen: verdieping 1 tot en met 5, vak 1 tot en met 12


@pytest.mark.parametrize("verdieping, geldig", [(1, True), (5, True), (0, False), (6, False)],
                         ids=["1", "5", "0", "6"])
def test_grens_van_de_verdieping(app, verdieping, geldig):
    if geldig:
        assert codes(rek(vakken={(verdieping, 1)})) == [f"A/{verdieping}/1"]
    else:
        with pytest.raises(Regelfout, match="verdieping 1 tot en met 5 en vak 1 tot en met 12"):
            rek(vakken={(verdieping, 1)})
        assert aantal(Rek) == 0 and acties() == []


@pytest.mark.parametrize("vak, geldig", [(1, True), (12, True), (0, False), (13, False)],
                         ids=["1", "12", "0", "13"])
def test_grens_van_het_vak(app, vak, geldig):
    if geldig:
        assert codes(rek(vakken={(1, vak)})) == [f"A/1/{vak}"]
    else:
        with pytest.raises(Regelfout, match="verdieping 1 tot en met 5 en vak 1 tot en met 12"):
            rek(vakken={(1, vak)})
        assert aantal(Rek) == 0


@pytest.mark.parametrize("vakken", [{(0, 0)}, {(1, 1), (6, 1)}, {("a", 1)}, {(None, None)}],
                         ids=["nul_nul", "een_ongeldig_tussen_geldige", "tekst", "none"])
def test_misvormd_vak_geeft_een_melding_van_het_domein(app, vakken):
    with pytest.raises(Regelfout, match="verdieping 1 tot en met 5"):
        rek(vakken=vakken)
    r = rek()
    with pytest.raises(Regelfout, match="verdieping 1 tot en met 5"):
        indeling.indeling_instellen(r.id, vakken, CLI)
    assert codes(r) == ["A/1/1", "A/1/2"]


def test_lege_set_geweigerd(app):
    with pytest.raises(Regelfout, match="minstens één vak"):
        rek(vakken=set())
    r = rek()
    with pytest.raises(Regelfout, match="minstens één vak"):
        indeling.indeling_instellen(r.id, set(), CLI)
    assert codes(r) == ["A/1/1", "A/1/2"]


def test_een_rek_met_alle_vakken_van_alle_verdiepingen(app):
    r = rek(vakken={(v, k) for v in range(1, 6) for k in range(1, 13)})
    assert len(r.plaatsen) == 60


# Instellen: aan, uit, gaten


def test_aanzetten_maakt_plaatsen_zonder_instellingen_en_laat_de_rest_staan(app):
    r = rek()
    oud = indeling.rek(r.id).plaatsen[0]
    indeling.plaats_wijzigen(oud.id, [1, 2], True, CLI)
    sleutel = oud.publieke_sleutel
    indeling.indeling_instellen(r.id, {(1, 1), (1, 2), (2, 5)}, CLI)
    p11, _p12, nieuw = indeling.rek(r.id).plaatsen
    assert nieuw.code == "A/2/5" and nieuw.is_clubplaats is False and nieuw.bootsoorten == []
    assert nieuw.boot_id is None and len(nieuw.publieke_sleutel) == 10
    assert (p11.id, p11.publieke_sleutel, p11.is_clubplaats) == (oud.id, sleutel, True)
    assert len(p11.bootsoorten) == 2


def test_uitzetten_zonder_boot_verwijdert_de_plaats_en_laat_een_gat(app):
    r = rek(vakken={(1, 1), (1, 2), (1, 3), (2, 1)})
    sleutels = {p.code: p.publieke_sleutel for p in indeling.rek(r.id).plaatsen}
    indeling.indeling_instellen(r.id, {(1, 1), (1, 3), (2, 1)}, CLI)
    r = indeling.rek(r.id)
    assert [p.code for p in r.plaatsen] == ["A/1/1", "A/1/3", "A/2/1"]  # A/1/3 houdt zijn nummer
    assert {p.code: p.publieke_sleutel for p in r.plaatsen} == {
        c: s for c, s in sleutels.items() if c != "A/1/2"}


def test_een_gat_in_de_nummering_en_een_lege_verdieping(app):
    """A/1 met vak 1, 3, 4 en 6 (de echte indeling); verdieping 2 uitzetten laat 1 staan."""
    r = rek(vakken={(1, 1), (1, 3), (1, 4), (1, 6), (2, 1), (2, 2)})
    assert codes(r) == ["A/1/1", "A/1/3", "A/1/4", "A/1/6", "A/2/1", "A/2/2"]
    indeling.indeling_instellen(r.id, {(1, 1), (1, 3), (1, 4), (1, 6)}, CLI)
    assert codes(r) == ["A/1/1", "A/1/3", "A/1/4", "A/1/6"]  # verdieping 2 bestaat niet meer
    indeling.indeling_instellen(r.id, {(1, 1), (1, 3), (1, 4), (1, 6), (2, 1)}, CLI)
    assert codes(r)[-1] == "A/2/1"  # en kan terugkomen, zonder nummering te schuiven


def test_uitzetten_met_boot_geweigerd_en_er_verandert_niets(app):
    r = rek(vakken={(1, 1), (1, 2), (1, 3)})
    p = indeling.rek(r.id).plaatsen[1]
    indeling.plaats_wijzigen(p.id, [1], False, CLI)
    toewijzing.toewijzen(p.id, boot(lid().id).id, CLI)
    voor = acties()
    with pytest.raises(Regelfout, match=r"Op plaats A/1/2 ligt een boot\. Geef de plaats eerst vrij"):
        indeling.indeling_instellen(r.id, {(1, 1), (2, 4)}, CLI)  # ook 1/3 uit en 2/4 aan
    db.session.expire_all()
    assert codes(r) == ["A/1/1", "A/1/2", "A/1/3"] and acties() == voor
    assert db.session.get(Plaats, p.id).boot_id is not None


def test_zelfde_vakken_instellen_verandert_niets(app):
    r = rek()
    voor = acties()
    indeling.indeling_instellen(r.id, {(1, 1), (1, 2)}, CLI)
    assert codes(r) == ["A/1/1", "A/1/2"] and acties() == voor


def test_onbekend_rek_instellen(app):
    with pytest.raises(Regelfout, match="Dit rek bestaat niet"):
        indeling.indeling_instellen(999, {(1, 1)}, CLI)


# Reknaam en omschrijving


@pytest.mark.parametrize("naam", ["A/B", "/", "", "   ", "x" * 11], ids=[
    "schuine_streep_midden", "schuine_streep_alleen", "leeg", "spaties", "elf_tekens"])
def test_ongeldige_reknaam_geweigerd(app, naam):
    with pytest.raises(Regelfout, match="naam van 1 tot 10 tekens, zonder /"):
        rek(naam)
    assert aantal(Rek) == 0
    r = rek("B")
    with pytest.raises(Regelfout, match="naam van 1 tot 10 tekens, zonder /"):
        indeling.rek_wijzigen(r.id, naam, "", CLI)
    assert indeling.rek(r.id).naam == "B"


@pytest.mark.parametrize("naam, verwacht", [("x", "x"), ("x" * 10, "x" * 10), ("  Noord ", "Noord")],
                         ids=["een_teken", "tien_tekens", "getrimd"])
def test_geldige_reknaam(app, naam, verwacht):
    assert rek(naam).naam == verwacht


@pytest.mark.parametrize("tweede", ["A", "a", " a "], ids=["gelijk", "kleine_letter", "met_spaties"])
def test_dubbele_reknaam_met_andere_hoofdletters_geweigerd(app, tweede):
    rek("A")
    with pytest.raises(Regelfout, match="Er is al een rek met de naam A"):
        rek(tweede)
    andere = rek("B")
    with pytest.raises(Regelfout, match="Er is al een rek met de naam A"):
        indeling.rek_wijzigen(andere.id, tweede, "", CLI)
    assert [r.naam for r in indeling.rekken()] == ["A", "B"]


def test_eigen_naam_met_andere_hoofdletters_mag(app):
    r = rek("A")
    indeling.rek_wijzigen(r.id, "a", "", CLI)
    assert indeling.rek(r.id).naam == "a"


def test_database_weigert_dubbele_reknaam_met_andere_hoofdletters(app, database):
    """Twee gelijktijdige aanvragen komen allebei langs de controle in Python; de database niet."""
    rek("A")
    with pytest.raises(IntegrityError, match="uq_rek_naam"), database.begin() as c:
        c.execute(text("INSERT INTO rek (naam) VALUES ('a')"))


@pytest.mark.parametrize("sql, constraint", [
    ("INSERT INTO plaats (rek_id, verdieping, vak, publieke_sleutel) VALUES (:r, 6, 1, 'xxxxxxxxxx')",
     "verdieping_geldig"),
    ("INSERT INTO plaats (rek_id, verdieping, vak, publieke_sleutel) VALUES (:r, 0, 1, 'xxxxxxxxxx')",
     "verdieping_geldig"),
    ("INSERT INTO plaats (rek_id, verdieping, vak, publieke_sleutel) VALUES (:r, 1, 13, 'xxxxxxxxxx')",
     "vak_geldig"),
    ("INSERT INTO plaats (rek_id, verdieping, vak, publieke_sleutel) VALUES (:r, 1, 0, 'xxxxxxxxxx')",
     "vak_geldig"),
    ("INSERT INTO plaats (rek_id, verdieping, vak, publieke_sleutel) VALUES (:r, 1, 1, 'xxxxxxxxxx')",
     "uq_plaats_rek_verdieping_vak"),
    ("INSERT INTO rek (naam) VALUES ('A/B')", "naam_geldig"),
    ("INSERT INTO rek (naam) VALUES ('')", "naam_geldig"),
    ("INSERT INTO rek (naam) VALUES ('elf tekens!')", "value too long"),
], ids=["verdieping_6", "verdieping_0", "vak_13", "vak_0", "dubbel_vak", "naam_met_streep",
        "naam_leeg", "naam_elf_tekens"])
def test_database_bewaakt_de_grenzen_zelf(app, database, sql, constraint):
    r = rek("A", {(1, 1)})
    with pytest.raises((IntegrityError, DataError), match=constraint), database.begin() as c:
        c.execute(text(sql), {"r": r.id})


@pytest.mark.parametrize("omschrijving, verwacht", [
    ("", ""), ("x" * 60, "x" * 60), ("  Grote stelling ", "Grote stelling")],
    ids=["leeg", "zestig_tekens", "getrimd"])
def test_geldige_omschrijving(app, omschrijving, verwacht):
    r = rek(omschrijving=omschrijving)
    assert indeling.rek(r.id).omschrijving == verwacht
    indeling.rek_wijzigen(r.id, "B", "y", CLI)
    indeling.rek_wijzigen(r.id, "B", omschrijving, CLI)
    assert indeling.rek(r.id).omschrijving == verwacht


def test_omschrijving_van_61_tekens_geweigerd(app):
    with pytest.raises(Regelfout, match="hooguit 60 tekens"):
        rek(omschrijving="x" * 61)
    assert aantal(Rek) == 0
    r = rek()
    with pytest.raises(Regelfout, match="hooguit 60 tekens"):
        indeling.rek_wijzigen(r.id, "A", "x" * 61, CLI)
    assert indeling.rek(r.id).omschrijving == ""


def test_hernoemen_houdt_sleutel_en_toewijzing_en_wijzigt_alle_aanduidingen(app):
    r = rek(vakken={(1, 1), (3, 12)})
    p = indeling.rek(r.id).plaatsen[0]
    indeling.plaats_wijzigen(p.id, [1], False, CLI)
    b = boot(lid().id)
    toewijzing.toewijzen(p.id, b.id, CLI)
    sleutels = [q.publieke_sleutel for q in indeling.rek(r.id).plaatsen]
    indeling.rek_wijzigen(r.id, "Noord", "Links", CLI)
    nieuw = indeling.rek(r.id)
    assert [q.code for q in nieuw.plaatsen] == ["Noord/1/1", "Noord/3/12"]
    assert [q.publieke_sleutel for q in nieuw.plaatsen] == sleutels
    assert nieuw.plaatsen[0].boot_id == b.id
    assert indeling.openbaar(sleutels[0])["code"] == "Noord/1/1"


# Volgorde: rek (volgorde van het rek), verdieping, vak


def test_volgorde_in_alle_lijsten(app):
    rek("B", {(2, 1), (1, 12), (1, 2), (1, 1)})  # B eerst gemaakt, dus voor A
    rek("A", {(2, 3), (1, 5)})
    verwacht = ["B/1/1", "B/1/2", "B/1/12", "B/2/1", "A/1/5", "A/2/3"]
    assert [p.code for r in indeling.rekken() for p in r.plaatsen] == verwacht
    assert [p.code for p in indeling.vrije_plaatsen()] == verwacht
    assert [k["code"] for k in indeling.kaartjes(alle=True)] == verwacht
    assert [p["code"] for p in uitlezen.plaatsen()] == verwacht


def test_export_in_de_volgorde_van_de_loods(app):
    import io

    from openpyxl import load_workbook
    rek("B", {(2, 1), (1, 12), (1, 2)})
    rek("A", {(1, 1)})
    blad = load_workbook(io.BytesIO(indeling.export("Botenloods"))).active
    assert [(rij[0].value, rij[1].value) for rij in blad.iter_rows(min_row=2)] == [
        ("B", "B/1/2"), ("B", "B/1/12"), ("B", "B/2/1"), ("A", "A/1/1")]


def test_kaartjes_en_openbare_pagina_tonen_de_omschrijving_van_het_rek(app):
    r = rek(omschrijving="Grote botenloods stelling links")
    p = indeling.rek(r.id).plaatsen[0]
    [kaartje] = indeling.kaartjes(plaats_ids=[p.id])
    assert kaartje["omschrijving"] == "Grote botenloods stelling links" and kaartje["code"] == "A/1/1"
    assert indeling.openbaar(p.publieke_sleutel)["omschrijving"] == "Grote botenloods stelling links"
    # Er komen geen velden bij in de API (issue #80): de plaatsen houden dezelfde vijf sleutels.
    assert set(uitlezen.plaatsen()[0]) == {"code", "rek", "clubplaats", "bootsoorten", "boot"}


# Logregels


def regels(actie):
    return db.session.scalars(select(Logregel).where(Logregel.actie == actie)
                              .order_by(Logregel.id)).all()


def test_logregels_van_aanmaken_instellen_en_wijzigen(app):
    r = rek("A", {(1, 1), (1, 2)}, "Links")
    [aangemaakt] = regels("rek.aangemaakt")
    assert aangemaakt.gegevens == {"naam": "A", "omschrijving": "Links", "vakken": 2}
    assert aangemaakt.verwijzingen == [f"rek:{r.id}"]
    assert [x.gegevens for x in regels("plaats.aangemaakt")] == [
        {"plaatscode": "A/1/1"}, {"plaatscode": "A/1/2"}]
    assert all(f"rek:{r.id}" in x.verwijzingen for x in regels("plaats.aangemaakt"))
    weg = indeling.rek(r.id).plaatsen[0]
    indeling.indeling_instellen(r.id, {(1, 2), (4, 4)}, CLI)
    [verwijderd] = regels("plaats.verwijderd")
    assert verwijderd.gegevens == {"plaatscode": "A/1/1"}
    assert verwijderd.verwijzingen == [f"plaats:{weg.id}", f"rek:{r.id}"]
    assert regels("plaats.aangemaakt")[-1].gegevens == {"plaatscode": "A/4/4"}
    indeling.rek_wijzigen(r.id, "B", "Rechts", CLI)
    assert regels("rek.gewijzigd")[-1].gegevens == {"naam": ["A", "B"],
                                                    "omschrijving": ["Links", "Rechts"]}
    voor = len(acties())
    indeling.rek_wijzigen(r.id, "B", "Rechts", CLI)
    assert len(acties()) == voor
    # Alleen wat veranderde, per veld.
    indeling.rek_wijzigen(r.id, "B", "", CLI)
    assert regels("rek.gewijzigd")[-1].gegevens == {"omschrijving": ["Rechts", ""]}


def test_een_weigering_geeft_geen_logregel(app):
    rek("A")
    voor = acties()
    for fout in (lambda: rek("A"), lambda: rek("x/y"), lambda: rek("B", {(9, 9)}),
                 lambda: rek("B", omschrijving="x" * 61)):
        with pytest.raises(Regelfout):
            fout()
    assert acties() == voor


# Races van indeling_instellen: FOR UPDATE op het rek en op de plaatsen (ADR-003)


def gevuld_rek():
    r = rek("A", {(1, 1), (1, 2)})
    return r, indeling.rek(r.id).plaatsen[0], boot(lid().id)


def test_gelijktijdig_toewijzen_en_uitzetten(app):
    """Een toewijzing houdt de plaats vast. Uitzetten wacht daarop en ziet daarna de boot. Zonder
    FOR UPDATE op de plaatsen wacht het niet, en verdwijnt de plaats met de boot."""
    r, p, b = gevuld_rek()
    fouten = race(app, ["SELECT id FROM plaats WHERE id = :p FOR UPDATE",
                        "UPDATE plaats SET boot_id = :b WHERE id = :p"], {"p": p.id, "b": b.id},
                  lambda: indeling.indeling_instellen(r.id, {(1, 2)}, CLI))
    assert fouten == ["Op plaats A/1/1 ligt een boot. Geef de plaats eerst vrij."]
    assert codes(r) == ["A/1/1", "A/1/2"] and db.session.get(Plaats, p.id).boot_id == b.id
    assert "plaats.verwijderd" not in acties()


def test_uitzetten_ziet_de_boot_ook_als_de_plaats_al_geladen_was(app):
    """De actie laadt de plaats eerst zonder slot (verouderde boot_id: leeg); populate_existing
    haalt de nieuwe toestand na het slot binnen."""
    r, p, b = gevuld_rek()

    def actie():
        # Vasthouden: anders ruimt de identity map de plaats op en laadt de query hem vers.
        geladen = db.session.get(Plaats, p.id)
        assert geladen.boot_id is None
        indeling.indeling_instellen(r.id, {(1, 2)}, CLI)

    fouten = race(app, ["SELECT id FROM plaats WHERE id = :p FOR UPDATE",
                        "UPDATE plaats SET boot_id = :b WHERE id = :p"], {"p": p.id, "b": b.id},
                  actie)
    assert fouten == ["Op plaats A/1/1 ligt een boot. Geef de plaats eerst vrij."]
    assert db.session.get(Plaats, p.id).boot_id == b.id


def test_twee_keer_gelijktijdig_hetzelfde_vak_aanzetten(app):
    """De tweede aanvraag wacht op het slot van het rek en ziet daarna het nieuwe vak; zonder
    slot op het rek probeert ze het vak nog eens aan te maken en geeft de unieke constraint een
    fout."""
    r, _p, _b = gevuld_rek()
    sql = ["SELECT id FROM rek WHERE id = :r FOR UPDATE",
           ("INSERT INTO plaats (rek_id, verdieping, vak, publieke_sleutel) "
            "VALUES (:r, 2, 2, 'zzzzzzzzzz')")]
    onverwacht = []

    def actie():
        try:
            indeling.indeling_instellen(r.id, {(1, 1), (1, 2), (2, 2)}, CLI)
        except Regelfout:
            raise
        except Exception as fout:  # noqa: BLE001  race() vangt alleen Regelfouten; de thread zou stil sterven
            onverwacht.append(repr(fout))

    fouten = race(app, sql, {"r": r.id}, actie)
    assert fouten == [] and onverwacht == []
    nieuw = indeling.rek(r.id).plaatsen
    assert [p.code for p in nieuw] == ["A/1/1", "A/1/2", "A/2/2"]
    assert nieuw[-1].publieke_sleutel == "zzzzzzzzzz"
