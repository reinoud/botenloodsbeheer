"""Migratie omkeerbaar en gelijk aan de modellen; heartbeat van de worker; seed."""

from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app import seed, taken
from app.domein import CLI, leden, wachtlijst
from app.models import Boot, Lid, Logregel, Plaats, Rek, Taakrun, Wachtlijst, db
from tests.unit.conftest import nieuwe_database
from tests.unit.hulp import als_api
from tests.unit.test_leden import FIXTURE


def test_migratie_omkeerbaar_en_gelijk_aan_modellen(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "head")
    command.check(cfg)  # faalt als models.py en de migraties uit elkaar lopen
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


def rechten_taken(cfg, rol="botenloods_taken"):
    """De tabel- en reeksrechten van rol in de database van cfg."""
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as c:
        rijen = c.execute(text(
            "SELECT table_name, privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee = :rol "
            "UNION ALL SELECT sequencename, 'USAGE' FROM pg_sequences WHERE has_sequence_privilege("
            ":rol, quote_ident(schemaname) || '.' || quote_ident(sequencename), "
            "'USAGE')"), {"rol": rol}).all()
    engine.dispose()
    return set(rijen)


def test_migratie_0010_beperkt_rechten_taken_en_downgrade_zet_ze_terug(database):
    """#60: de downgrade geeft precies de rechten van 0009 terug."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0009")
    oud = rechten_taken(cfg)
    command.upgrade(cfg, "0015")
    nieuw = rechten_taken(cfg)
    assert nieuw < oud and ("beheerder", "INSERT") in oud - nieuw
    command.downgrade(cfg, "0009")
    assert rechten_taken(cfg) == oud


def test_migratie_0013_trekt_delete_op_verdieping_bootsoort_in_voor_web(database):
    """Issue #85: de cascades draaien als eigenaar, dus web heeft DELETE niet nodig."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0012")
    oud = rechten_taken(cfg, "botenloods_web")
    assert ("verdieping_bootsoort", "DELETE") in oud
    command.upgrade(cfg, "0015")
    assert rechten_taken(cfg, "botenloods_web") == oud - {("verdieping_bootsoort", "DELETE")}
    command.downgrade(cfg, "0012")
    assert rechten_taken(cfg, "botenloods_web") == oud


def test_migratie_0011_geeft_taken_insert_op_bootsoort_en_downgrade_trekt_het_in(database):
    """Issue #80: flask seed voegt de bootsoort Wildwaterkano toe, als botenloods_taken."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0010")
    oud = rechten_taken(cfg)
    nieuw_recht = {("bootsoort", "INSERT"), ("bootsoort_id_seq", "USAGE")}
    assert not nieuw_recht & oud
    command.upgrade(cfg, "0015")
    assert rechten_taken(cfg) == oud | nieuw_recht
    command.downgrade(cfg, "0010")
    assert rechten_taken(cfg) == oud


def test_migratie_0011_verwijdert_plaatsen_en_downgrade_behoudt_ze_met_aanduiding(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0010")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.begin() as c:
        c.execute(text("INSERT INTO rek (naam, volgorde) VALUES ('Rek oud', 1)"))
        c.execute(text("INSERT INTO plaats (rek_id, code, publieke_sleutel, volgorde) "
                       "SELECT id, 'A01', 'sleutel001', 1 FROM rek"))
    command.upgrade(cfg, "head")
    with engine.begin() as c:
        assert c.scalar(text("SELECT count(*) FROM plaats")) == 0
        assert c.scalar(text("SELECT count(*) FROM rek")) == 0
        c.execute(text("INSERT INTO rek (naam, omschrijving, volgorde) VALUES ('B', 'Links', 1)"))
        c.execute(text("INSERT INTO plaats (rek_id, verdieping, vak, publieke_sleutel) "
                       "SELECT id, 2, 5, 'sleutel002' FROM rek"))
    command.downgrade(cfg, "0010")
    with engine.connect() as c:
        assert c.execute(text("SELECT code, volgorde FROM plaats")).all() == [("B/2/5", 17)]
    command.upgrade(cfg, "head")
    engine.dispose()


def test_migratie_0004_verwijdert_geupload_logo(database):
    """BLB-027 criterium 5: een logo uit slice 3 verdwijnt; alleen het logo uit de installatie
    gold toen nog (sinds 0017 staat het logo weer in de database). Foto's blijven staan."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0003")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    rij = ("INSERT INTO afbeelding (soort, mime_type, inhoud, breedte, hoogte, sleutel) "
           "VALUES (:s, 'image/png', '\\x00', 1, 1, :s) RETURNING id")
    with engine.begin() as c:
        logo = c.execute(text(rij), {"s": "logo"}).scalar()
        c.execute(text(rij), {"s": "foto"})
        c.execute(text("INSERT INTO instelling (sleutel, waarde) VALUES ('logo', :id), "
                       "('naam', 'KV')"), {"id": str(logo)})
    command.upgrade(cfg, "0004")
    with engine.connect() as c:
        assert c.execute(text("SELECT soort FROM afbeelding")).scalars().all() == ["foto"]
        assert c.execute(text("SELECT sleutel FROM instelling")).scalars().all() == ["naam"]
        with pytest.raises(IntegrityError):
            c.execute(text(rij), {"s": "logo"})
    command.downgrade(cfg, "0003")
    with engine.begin() as c:
        c.execute(text(rij), {"s": "logo"})
    engine.dispose()


def test_migratie_0015_verwijdert_de_kleurrijen_en_laat_de_naam(database):
    """Issue #150: de instelbare kleuren vervallen. De downgrade herstelt niets en faalt niet."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0014")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.begin() as c:
        c.execute(text("INSERT INTO instelling (sleutel, waarde) VALUES ('naam', 'KV'), "
                       "('kleur_primair', '#123456'), ('kleur_secundair', '#654321')"))
    command.upgrade(cfg, "head")
    with engine.connect() as c:
        assert c.execute(text("SELECT sleutel FROM instelling")).scalars().all() == ["naam"]
    command.downgrade(cfg, "0014")
    with engine.connect() as c:
        assert c.execute(text("SELECT sleutel FROM instelling")).scalars().all() == ["naam"]
    engine.dispose()


def test_precies_een_migratiehead(database):
    scripts = ScriptDirectory.from_config(nieuwe_database("botenloods_migratie"))
    assert scripts.get_heads() == ["0019"]


@pytest.mark.parametrize("sql", ["INSERT INTO lid (lidnummer, naam) VALUES ('9', 'X')",
                                 "UPDATE lid SET naam = 'X'", "DELETE FROM lid"])
def test_webgebruiker_leest_leden_alleen(app, sql):
    db.session.execute(select(Lid)).all()
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(sql))
    db.session.rollback()


@pytest.mark.worker  # de tweede hartslag is een UPDATE op taakrun als botenloods_taken (#60)
def test_heartbeat(app):
    assert not taken.gezond()
    taken.hartslag()
    taken.hartslag()
    assert taken.gezond()
    assert len(db.session.scalars(select(Taakrun)).all()) == 1
    db.session.scalar(select(Taakrun)).beeindigd_op = datetime.now(UTC) - timedelta(minutes=3)
    db.session.commit()
    assert not taken.gezond()


@pytest.mark.api
def test_api_kan_de_hartslag_niet_wijzigen_of_aanmaken(app, database):
    """Issue #24: het rijbeleid op taakrun laat de API alleen zijn eigen taken zien en wijzigen."""
    with database.begin() as c:
        c.execute(text("INSERT INTO taakrun (taak, status, beeindigd_op) "
                       "VALUES ('heartbeat', 'geslaagd', now() - interval '1 hour')"))
    wijziging = db.session.execute(text("UPDATE taakrun SET beeindigd_op = now()"))
    assert wijziging.rowcount == 0, "de API wijzigde de hartslag"
    assert db.session.execute(text("SELECT 1 FROM taakrun")).all() == []
    db.session.rollback()
    with pytest.raises(ProgrammingError, match="row-level security"):
        db.session.execute(text("INSERT INTO taakrun (taak, status) VALUES ('heartbeat', 'geslaagd')"))
    db.session.rollback()
    db.session.execute(text("INSERT INTO taakrun (taak, status) VALUES ('ledenimport', 'mislukt')"))
    db.session.rollback()


@pytest.mark.worker  # seed draait in de worker (#9); de leden komen uit de import (ADR-012)
def test_seed_maakt_de_synthetische_loods(app):
    with pytest.raises(seed.SeedFout, match="nog geen leden"):
        seed.seed(echo=lambda _: None)
    als_api(leden.importeer, FIXTURE, CLI)
    seed.seed(echo=lambda _: None)

    def tel(model, *waar):
        return db.session.scalar(select(func.count()).select_from(model).where(*waar))

    assert tel(Rek) == 11 and tel(Plaats) == 229 and tel(Plaats, Plaats.is_clubplaats) == 30
    _controleer_bootsoort_per_vak()
    assert tel(Lid) == 208 and tel(Boot) == 180 and tel(Boot, Boot.lid_id.is_(None)) == 6
    assert tel(Plaats, Plaats.boot_id.isnot(None)) == 150
    oud_met_plaats = [p for p in db.session.scalars(select(Plaats).where(Plaats.boot_id.isnot(None)))
                      if p.boot.lid and leden.is_oud_lid(p.boot.lid)]
    assert len(oud_met_plaats) == 4
    # #10: elke boot en elke toewijzing staat in het log, ook die van oud-leden.
    assert tel(Logregel, Logregel.actie == "boot.aangemaakt") == 180
    assert tel(Logregel, Logregel.actie == "plaats.toegewezen") == 150
    # §6.3: 10 boten van leden op de wachtlijst, verdeeld over minstens drie bootsoorten.
    rijen = wachtlijst.lijsten()
    assert sum(len(rij) for _s, rij in rijen) == tel(Wachtlijst) == 10 and len(rijen) >= 3
    assert tel(Logregel, Logregel.actie == "wachtlijst.toegevoegd") == 10
    seed.seed(echo=lambda _: None)  # tweede keer: niets
    assert tel(Rek) == 11 and tel(Plaats) == 229


def _controleer_bootsoort_per_vak():
    """De bootsoorten en clubplaatsen van de stakeholder (#80, opmerking 2026-11-03 18:29),
    onafhankelijk van de CSV opgeschreven."""
    canadees_op_1 = set("ABCDEFGKL")
    for p in db.session.scalars(select(Plaats)):
        verwacht = ("Wildwaterkano" if p.rek.naam == "H"
                    else "C11" if (p.rek.naam, p.verdieping) == ("J", 1)
                    else "Surfski" if p.rek.naam == "J"
                    else "Canadese kano" if p.rek.naam in canadees_op_1 and p.verdieping == 1
                    else "Kajak")
        assert [s.naam for s in p.bootsoorten] == [verwacht], p.code
        assert p.is_clubplaats == (p.rek.naam == "A"), p.code
    assert {p.code for p in db.session.scalars(select(Plaats).where(Plaats.rek.has(naam="A"),
                                                                    Plaats.verdieping == 1))
            } == {f"A/1/{k}" for k in range(1, 7)}  # geen gaten (#94)
    assert db.session.scalar(select(Rek.omschrijving).where(Rek.naam == "H")) != ""


@pytest.mark.worker
def test_worker_mag_een_bootsoort_toevoegen(app):
    """Issue #80: INSERT op bootsoort en gebruik van bootsoort_id_seq (flask seed, Wildwaterkano)."""
    db.session.execute(text("INSERT INTO bootsoort (naam) VALUES ('X')"))
    db.session.rollback()


def test_seed_weigert_in_productie(app):
    app.config["APP_OMGEVING"] = "productie"
    with pytest.raises(seed.SeedFout):
        seed.seed()


@pytest.mark.parametrize("sql", [
    "INSERT INTO beheerder (naam, gebruikersnaam, actief, sessieversie) VALUES ('X', 'x', true, 1)",
    "UPDATE beheerder SET actief = false", "DELETE FROM beheerder",
    "SELECT 1 FROM passkey", "SELECT 1 FROM uitnodiging", "SELECT 1 FROM token", "UPDATE instelling SET waarde = 'x'",
    "DELETE FROM rek", "DELETE FROM plaats", "DELETE FROM bootsoort", "DELETE FROM taakrun"])
@pytest.mark.worker
def test_worker_heeft_geen_rechten_buiten_taken_en_seed(app, sql):
    """#60: de worker kan geen beheerder aanmaken of de indeling en instellingen wijzigen."""
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(sql))
    db.session.rollback()


def test_migratie_0017_laat_het_logo_toe_en_de_downgrade_verwijdert_het(database):
    """Issue #186: afbeelding laat weer soort logo toe. De downgrade verwijdert een geüpload logo
    (anders faalt de oude controle) en laat de foto's en de naam staan."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0016")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    rij = ("INSERT INTO afbeelding (soort, mime_type, inhoud, breedte, hoogte, sleutel) "
           "VALUES (:s, 'image/png', '\\x00', 1, 1, :s) RETURNING id")
    with engine.connect() as c, pytest.raises(IntegrityError):
        c.execute(text(rij), {"s": "logo"})  # vóór 0017 geweigerd
    command.upgrade(cfg, "0017")
    with engine.begin() as c:
        logo = c.execute(text(rij), {"s": "logo"}).scalar()
        c.execute(text(rij), {"s": "foto"})
        c.execute(text("INSERT INTO instelling (sleutel, waarde) VALUES ('logo', :id), "
                       "('naam', 'KV')"), {"id": str(logo)})
    command.downgrade(cfg, "0016")
    with engine.connect() as c:
        assert c.execute(text("SELECT soort FROM afbeelding")).scalars().all() == ["foto"]
        assert c.execute(text("SELECT sleutel FROM instelling")).scalars().all() == ["naam"]
    command.upgrade(cfg, "head")
    engine.dispose()


def test_migratie_0018_haalt_contactgegevens_en_het_recht_weg_en_trekt_tokens_in(database):
    """Issue #180: de kolommen vervallen. Een actief token met alleen persoonsgegevens wordt
    ingetrokken, met een logregel; een token met meer rechten verliest alleen dat recht; een
    ingetrokken token blijft zoals het was (de check eist één recht). De downgrade zet de
    kolommen leeg terug en haalt niets van de rest terug."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0017")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    token = ("INSERT INTO token (naam, soort, prefix, hash, rechten, ip_whitelist, verloopt_op, "
             "ingetrokken_op, gemaakt_door) VALUES (:n, 'robot', :n, 'x', CAST(:r AS text[]), '{10.0.0.0/8}', now(), "
             "CASE WHEN :i THEN now() END, 'cli')")
    with engine.begin() as c:
        c.execute(text("INSERT INTO lid (lidnummer, naam, adres, telefoon, email) "
                       "VALUES ('1', 'Anna', 'Proefweg 1', '06-1', 'a@b.nl')"))
        for naam, rechten, ingetrokken in [("alleen", "{persoonsgegevens}", False),
                                           ("meer", "{persoonsgegevens,leden:lezen}", False),
                                           ("oud", "{persoonsgegevens}", True),
                                           ("andere", "{boten:lezen}", False)]:
            c.execute(text(token), {"n": naam, "r": rechten, "i": ingetrokken})
    command.upgrade(cfg, "0018")
    with engine.connect() as c:
        kolommen = c.execute(text("SELECT column_name FROM information_schema.columns "
                                  "WHERE table_name = 'lid'")).scalars().all()
        assert not {"adres", "telefoon", "email"} & set(kolommen) and "lid_sinds" in kolommen
        rijen = {n: (r, i) for n, r, i in c.execute(text(
            "SELECT naam, rechten, ingetrokken_op IS NOT NULL FROM token"))}
        assert rijen == {"alleen": (["persoonsgegevens"], True), "meer": (["leden:lezen"], False),
                         "oud": (["persoonsgegevens"], True), "andere": (["boten:lezen"], False)}
        [regel] = c.execute(text("SELECT soort, actor_soort, actor_naam, actie, verwijzingen, gegevens "
                                 "FROM logregel")).all()
        alleen = c.execute(text("SELECT id FROM token WHERE naam = 'alleen'")).scalar()
        assert regel == ("mutatie", "systeem", "migratie", "token.ingetrokken", [f"token:{alleen}"],
                         {"naam": "alleen", "reden": "recht persoonsgegevens vervallen (#180)"})
    command.downgrade(cfg, "0017")
    with engine.connect() as c:
        assert c.execute(text("SELECT adres, telefoon, email, naam FROM lid")).all() == [
            (None, None, None, "Anna")]
        assert c.execute(text("SELECT count(*) FROM token WHERE ingetrokken_op IS NOT NULL")).scalar() == 2
    command.upgrade(cfg, "head")
    engine.dispose()


def test_migratie_0019_maakt_boten_zonder_lid_clubboot_en_de_controle_sluit_lid_en_clubboot_uit(database):
    """Issue #204: elke bestaande boot zonder lid wordt clubboot, een boot met een lid blijft
    zoals hij was. De controle weigert lid en clubboot samen; geen lid en geen clubboot (onbekend)
    mag. De downgrade haalt kolom en controle weg."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0018")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.begin() as c:
        c.execute(text("INSERT INTO lid (lidnummer, naam) VALUES ('1', 'Anna')"))
        soort = c.execute(text("SELECT id FROM bootsoort ORDER BY id LIMIT 1")).scalar()
        c.execute(text("INSERT INTO boot (naam, bootsoort_id, lid_id) VALUES ('Club', :s, NULL)"), {"s": soort})
        c.execute(text("INSERT INTO boot (naam, bootsoort_id, lid_id) "
                       "VALUES ('Eigen', :s, (SELECT id FROM lid))"), {"s": soort})
    command.upgrade(cfg, "0019")
    with engine.connect() as c:
        assert dict(c.execute(text("SELECT naam, clubboot FROM boot")).all()) == {"Club": True, "Eigen": False}
    with engine.begin() as c:  # geen lid en geen clubboot: eigenaar onbekend
        c.execute(text("INSERT INTO boot (naam, bootsoort_id) VALUES ('Onbekend', :s)"), {"s": soort})
    with pytest.raises(IntegrityError, match="lid_of_clubboot"), engine.begin() as c:
        c.execute(text("INSERT INTO boot (naam, bootsoort_id, lid_id, clubboot) "
                       "VALUES ('Beide', :s, (SELECT id FROM lid), true)"), {"s": soort})
    command.downgrade(cfg, "0018")
    with engine.connect() as c:
        kolommen = c.execute(text("SELECT column_name FROM information_schema.columns "
                                  "WHERE table_name = 'boot'")).scalars().all()
        assert "clubboot" not in kolommen
        assert c.execute(text("SELECT count(*) FROM boot")).scalar() == 3
    command.upgrade(cfg, "head")
    engine.dispose()
