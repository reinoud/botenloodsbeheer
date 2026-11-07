"""Migratie 0016, de rechten per rol, de cascades en de opschoning van de lopende bezettingsimport
en de onthouden koppelingen (issue #158, ADR-014 §3 en §4)."""

from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.domein import CLI, Actor, beheerders, bezetting_csv, leden, opschonen
from app.models import Bezettingsimport, Lid, Naamkoppeling, db
from tests.unit.conftest import nieuwe_database
from tests.unit.hulp import beheerder_met_wachtwoord, lid
from tests.unit.test_migratie_en_taken import rechten_taken
from tests.unit.test_tokens import eigenaar

TABELLEN = ("bezettingsimport", "naamkoppeling")


def tabellen(cfg):
    from sqlalchemy import create_engine

    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    namen = set(inspect(engine).get_table_names()) & set(TABELLEN)
    engine.dispose()
    return namen


def test_migratie_0016_upgrade_downgrade_upgrade_met_de_rechten_van_adr_014(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0015")
    assert not tabellen(cfg)
    voor = {rol: rechten_taken(cfg, rol) for rol in ("botenloods_web", "botenloods_taken", "botenloods_api")}
    command.upgrade(cfg, "head")
    assert tabellen(cfg) == set(TABELLEN)
    web, taken, api = (rechten_taken(cfg, rol) for rol in ("botenloods_web", "botenloods_taken", "botenloods_api"))
    assert web - voor["botenloods_web"] == {
        (t, r) for t in TABELLEN for r in ("SELECT", "INSERT", "UPDATE", "DELETE")
    } | {("bezettingsimport_id_seq", "USAGE"), ("naamkoppeling_id_seq", "USAGE")}
    assert taken - voor["botenloods_taken"] == {(t, r) for t in TABELLEN for r in ("SELECT", "DELETE")}
    assert api == voor["botenloods_api"]  # de API krijgt niets
    command.downgrade(cfg, "0015")
    assert not tabellen(cfg)
    assert {rol: rechten_taken(cfg, rol) for rol in voor} == voor  # de rechten verdwijnen met de tabellen
    command.upgrade(cfg, "head")
    assert tabellen(cfg) == set(TABELLEN)
    assert rechten_taken(cfg, "botenloods_web") == web and rechten_taken(cfg, "botenloods_taken") == taken


# De rechten: per recht een statement dat de rol echt uitvoert. Ontbreekt het recht, dan valt de test.

LEZEN_SCHRIJVEN = {
    "select-bezettingsimport": "SELECT id FROM bezettingsimport",
    "select-naamkoppeling": "SELECT id FROM naamkoppeling",
    "insert-bezettingsimport": ("INSERT INTO bezettingsimport (beheerder_id, verloopt_op, regels) "
                                "SELECT id, now(), '[]' FROM beheerder LIMIT 1"),
    "insert-naamkoppeling": "INSERT INTO naamkoppeling (naam, clubboot) VALUES ('x', true)",
    "update-bezettingsimport": "UPDATE bezettingsimport SET keuzes = '{}'",
    "update-naamkoppeling": "UPDATE naamkoppeling SET gebruikt_op = now()",
    "delete-bezettingsimport": "DELETE FROM bezettingsimport",
    "delete-naamkoppeling": "DELETE FROM naamkoppeling",
}


@pytest.mark.parametrize("sql", LEZEN_SCHRIJVEN.values(), ids=LEZEN_SCHRIJVEN)
def test_web_heeft_select_insert_update_en_delete_op_beide_tabellen(app, sql):
    beheerder_met_wachtwoord()
    db.session.execute(text(sql))
    db.session.rollback()


@pytest.mark.parametrize("tabel", TABELLEN)
def test_web_heeft_gebruik_van_de_reeks_van_beide_tabellen(app, tabel):
    assert db.session.scalar(text(f"SELECT nextval('{tabel}_id_seq')")) >= 1
    db.session.rollback()


@pytest.mark.worker
@pytest.mark.parametrize("sql", [v for k, v in LEZEN_SCHRIJVEN.items() if k.startswith(("select", "delete"))],
                         ids=[k for k in LEZEN_SCHRIJVEN if k.startswith(("select", "delete"))])
def test_taken_heeft_select_en_delete_op_beide_tabellen(app, sql):
    db.session.execute(text(sql))
    db.session.rollback()


@pytest.mark.worker
@pytest.mark.parametrize("sql", [v for k, v in LEZEN_SCHRIJVEN.items() if k.startswith(("insert", "update"))],
                         ids=[k for k in LEZEN_SCHRIJVEN if k.startswith(("insert", "update"))])
def test_taken_mag_niets_aanmaken_of_wijzigen_in_beide_tabellen(app, sql):
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(sql))
    db.session.rollback()


@pytest.mark.api
@pytest.mark.parametrize("tabel", TABELLEN)
def test_api_heeft_geen_recht_op_beide_tabellen(app, tabel):
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(f"SELECT 1 FROM {tabel}"))
    db.session.rollback()


# Constraints


def test_hooguit_een_lopende_import_en_een_koppeling_is_een_lid_of_de_club(app):
    b = beheerder_met_wachtwoord()[0]
    basis = {"beheerder_id": b.id, "verloopt_op": datetime.now(UTC), "regels": []}
    db.session.add(Bezettingsimport(**basis))
    db.session.commit()
    for fout in (Bezettingsimport(**basis), Bezettingsimport(enige=False, **basis)):
        db.session.add(fout)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
    anna = lid()
    for kwargs in ({"naam": "x"}, {"naam": "x", "lid_id": anna.id, "clubboot": True}):  # geen van beide, allebei
        db.session.add(Naamkoppeling(**kwargs))
        with pytest.raises(IntegrityError, match="lid_of_clubboot"):
            db.session.commit()
        db.session.rollback()
    db.session.add_all([Naamkoppeling(naam="x", lid_id=anna.id)])
    db.session.commit()
    db.session.add(Naamkoppeling(naam="x", clubboot=True))  # de naam is uniek
    with pytest.raises(IntegrityError, match="naamkoppeling_naam_key"):
        db.session.commit()
    db.session.rollback()


# Cascades: in de database, niet via de ORM


def test_geen_orm_relatie_naar_de_nieuwe_tabellen_zonder_passive_deletes():
    from sqlalchemy import inspect as insp

    from app.models import Beheerder

    for model, doel in ((Lid, Naamkoppeling), (Beheerder, Bezettingsimport)):
        for relatie in insp(model).relationships:
            assert relatie.mapper.class_ is not doel or relatie.passive_deletes, (model, relatie)


@pytest.mark.worker
def test_de_opschoning_verwijdert_een_oud_lid_en_de_database_haalt_zijn_koppeling_weg(app):
    """Als botenloods_taken: de cascade draait met de rechten van de eigenaar van de tabel."""
    eigenaar("INSERT INTO lid (lidnummer, naam, opzegdatum) VALUES ('1001', 'Oud', '2000-01-01'), "
             "('1002', 'Blijft', NULL)")
    eigenaar("INSERT INTO naamkoppeling (naam, lid_id) SELECT 'Ouwe', id FROM lid WHERE lidnummer = '1001'")
    eigenaar("INSERT INTO naamkoppeling (naam, lid_id) SELECT 'Bert', id FROM lid WHERE lidnummer = '1002'")
    eigenaar("INSERT INTO naamkoppeling (naam, clubboot) VALUES ('Club', true)")
    assert opschonen.draai()["leden"] == 1
    db.session.expire_all()
    assert {k.naam for k in db.session.scalars(select(Naamkoppeling))} == {"Bert", "Club"}
    assert db.session.scalar(select(Lid).where(Lid.lidnummer == "1001")) is None


def test_een_verwijderde_beheerder_neemt_de_lopende_import_mee(app):
    uploader = Actor.van(beheerder_met_wachtwoord("uploader")[0])
    collega = Actor.van(beheerder_met_wachtwoord("collega")[0])
    bezetting_csv.uploaden(b"plaats;boot;bootsoort;eigenaar;lidnummer\r\nA/1/1;Reiger;Kajak;;\r\n", uploader)
    beheerders.verwijderen(uploader.id, collega)
    assert db.session.scalar(select(Bezettingsimport)) is None


# Opschoning (ADR-014 §3)


def import_met_verlooptijd(verloopt):
    """De worker leest beheerder niet; de eigenaar maakt de beheerder en de import."""
    eigenaar("INSERT INTO beheerder (naam, gebruikersnaam, actief, sessieversie) VALUES ('U', 'u', true, 1)")
    eigenaar("INSERT INTO bezettingsimport (beheerder_id, verloopt_op, regels) "
             f"SELECT id, {verloopt}, '[]' FROM beheerder")


@pytest.mark.worker
def test_de_opschoning_verwijdert_verlopen_imports_en_koppelingen_van_vijf_jaar_en_telt_ze_in_taakrun(app):
    import_met_verlooptijd("now() - interval '1 second'")
    grens = datetime.now(UTC)
    for naam, dagen in (("oud", 5 * 365 + 2), ("net-te-oud", 5 * 365 + 1), ("net-goed", 5 * 365 - 3),
                        ("recent", 10)):
        eigenaar("INSERT INTO naamkoppeling (naam, clubboot, gebruikt_op) VALUES (:n, true, :t)",
                 n=naam, t=grens - timedelta(days=dagen))
    aantallen = opschonen.draai()
    assert (aantallen["imports"], aantallen["koppelingen"]) == (1, 2)
    db.session.expire_all()
    assert {k.naam for k in db.session.scalars(select(Naamkoppeling))} == {"net-goed", "recent"}
    assert db.session.scalar(select(Bezettingsimport)) is None
    run = db.session.scalar(text("SELECT aantallen FROM taakrun WHERE taak = 'opschoning'"))
    assert run["imports"] == 1 and run["koppelingen"] == 2


@pytest.mark.worker
def test_de_opschoning_laat_een_import_staan_die_nog_niet_verlopen_is(app):
    import_met_verlooptijd("now() + interval '1 minute'")
    assert opschonen.draai()["imports"] == 0
    db.session.expire_all()
    assert db.session.scalar(select(Bezettingsimport)) is not None


def test_de_bewaartermijn_van_koppelingen_is_de_bewaartermijn_van_de_rest():
    assert leden.BEWAARJAREN == 5 and bezetting_csv.VERLOOP == timedelta(hours=2)
    assert CLI
