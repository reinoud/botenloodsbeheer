"""Een account koppelen aan een lid (ADR-015, issue #353): koppelen, besluit 7, de racetest van de
afgeleide regel, de status en migratie 0023. De opschoning van kijkers staat in test_opschonen."""

from datetime import timedelta
from unittest import mock

import pytest
from alembic import command
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app import INT_MAX
from app.domein import CLI, Regelfout, beheerders, leden, vandaag
from app.models import Beheerder, Lid, db
from tests.unit.conftest import nieuwe_database
from tests.unit.hulp import lid, race
from tests.unit.test_gebruikers_rollen import actor, rol_van
from tests.unit.test_gebruikers_rollen import twee as _twee
from tests.unit.test_persoonlijke_tokens import logregels
from tests.unit.test_status_en_bootaantallen import ingelogd as _ingelogd
from tests.unit.test_status_en_bootaantallen import json_status
from tests.unit.test_tokens import eigenaar

twee = _twee  # fixtures
ingelogd = _ingelogd
OUD = ("bert is niet aan Oud gekoppeld: dat lid is oud-lid. Een kijker kan niet aan een oud-lid worden "
       "gekoppeld. Kies een ander lid of maak het account eerst beheerder.")
OUD_KIJKER = ("bert is niet kijker gemaakt: het gekoppelde lid is oud-lid. Een kijker met een oud-lid "
              "verwijdert de nachtelijke opschoning. Maak eerst de koppeling los of laat het account beheerder.")


def datum(dagen):
    return None if dagen is None else vandaag() + timedelta(days=dagen)


def morgen():
    return vandaag() + timedelta(days=1)


def lid_van(b):
    db.session.expire_all()
    return db.session.get(Beheerder, b.id).lid_id


def zeg_op(lid_, dag):
    eigenaar("UPDATE lid SET opzegdatum = :d WHERE id = :i", d=dag, i=lid_.id)


# oud_lid(dag): dezelfde regel als is_oud_lid


@pytest.mark.parametrize("dagen", [-1, 0, 1], ids=["gisteren", "vandaag", "morgen"])
@pytest.mark.parametrize("opzegdatum,uit_bron_op", [
    (None, None), (-1, None), (0, None), (1, None), (None, -1), (None, 0), (None, 1),
    (1, 0), (0, 1), (1, 1), (-1, 1), (1, -1)])
def test_oud_lid_als_sql_is_gelijk_aan_is_oud_lid(app, opzegdatum, uit_bron_op, dagen):
    """Ook op de grens: een opzegdatum van vandaag is al oud-lid, van morgen nog niet. Het twee-waardige
    resultaat blijft kloppen onder NOT, ook als een van de datums leeg is."""
    dag = vandaag() + timedelta(days=dagen)
    ld = lid(opzegdatum=datum(opzegdatum), uit_bron_op=datum(uit_bron_op))
    verwacht = leden.is_oud_lid(ld, dag)
    assert db.session.scalar(select(leden.oud_lid(dag)).where(Lid.id == ld.id)) is verwacht
    assert db.session.scalar(select(~leden.oud_lid(dag)).where(Lid.id == ld.id)) is (not verwacht)


# Koppelen en loskoppelen


def test_koppelen_en_loskoppelen_met_een_logregel_per_wijziging(app, twee):
    anna, _, bert = twee
    ld = lid("1001", "Lid een")
    assert beheerders.lid_koppelen(bert.id, ld.id, actor(anna)) == "bert"
    assert lid_van(bert) == ld.id
    [regel] = logregels("beheerder.lid_gewijzigd")
    assert regel.verwijzingen == [f"beheerder:{bert.id}", f"lid:{ld.id}"]
    assert regel.gegevens == {"gebruikersnaam": "bert", "lid": [None, f"lid:{ld.id}"]}
    assert regel.actor_naam == "anna"

    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))  # zonder verschil geen regel
    assert len(logregels("beheerder.lid_gewijzigd")) == 1

    beheerders.lid_koppelen(bert.id, None, actor(anna))
    assert lid_van(bert) is None
    laatste = logregels("beheerder.lid_gewijzigd")[-1]
    assert laatste.gegevens["lid"] == [f"lid:{ld.id}", None] and laatste.verwijzingen == [
        f"beheerder:{bert.id}", f"lid:{ld.id}"]
    beheerders.lid_koppelen(bert.id, None, actor(anna))
    assert len(logregels("beheerder.lid_gewijzigd")) == 2


def test_omkoppelen_naar_een_ander_lid_logt_oud_en_nieuw(app, twee):
    anna, _, bert = twee
    een, twee_ = lid("1", "Een"), lid("2", "Twee")
    beheerders.lid_koppelen(bert.id, een.id, actor(anna))
    beheerders.lid_koppelen(bert.id, twee_.id, actor(anna))
    assert logregels("beheerder.lid_gewijzigd")[-1].gegevens["lid"] == [f"lid:{een.id}", f"lid:{twee_.id}"]


def test_twee_accounts_aan_een_lid(app, twee):
    anna, _, bert = twee
    ld = lid()
    beheerders.lid_koppelen(anna.id, ld.id, actor(anna))
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    assert lid_van(anna) == lid_van(bert) == ld.id


@pytest.mark.parametrize("lid_id", [999, 0, -1, INT_MAX + 1])
def test_een_onbekend_lid_geeft_een_regelfout(app, twee, lid_id):
    anna, _, bert = twee
    with pytest.raises(Regelfout, match="Dit lid bestaat niet."):
        beheerders.lid_koppelen(bert.id, lid_id, actor(anna))
    assert lid_van(bert) is None


def test_een_kijker_koppelt_niemand(app, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(anna.id, "kijker", actor(bert))
    with pytest.raises(Regelfout, match="Alleen een beheerder wijzigt gebruikers."):
        beheerders.lid_koppelen(bert.id, lid().id, actor(anna))
    assert lid_van(bert) is None


def test_koppelen_van_een_onbekend_account(app, twee):
    with pytest.raises(Regelfout, match="Deze gebruiker bestaat niet."):
        beheerders.lid_koppelen(999, None, actor(twee[0]))


def test_een_geblokkeerd_account_blijft_koppelbaar(app, twee):
    anna, _, bert = twee
    beheerders.blokkeren(bert.id, actor(anna))
    ld = lid()
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    assert lid_van(bert) == ld.id


def test_een_lid_dat_tussen_controle_en_opslaan_verdwijnt_geeft_een_regelfout(app, twee):
    """De controle ziet het lid nog; de foreign key vangt de opschoning die ertussen kwam. Zonder die
    vangst volgt een IntegrityError, dus een fout 500."""
    anna, _, bert = twee
    spook = mock.Mock(spec=Lid, id=4242)
    with mock.patch.object(beheerders, "_lid", return_value=spook), \
            pytest.raises(Regelfout, match="Dit lid bestaat niet meer."):
        beheerders.lid_koppelen(bert.id, 4242, actor(anna))
    assert lid_van(bert) is None


def test_een_andere_integrityerror_dan_de_lidverwijzing_wordt_geen_regelfout(app, twee):
    """_lid_bestaat vangt alleen beheerder_lid_id_fkey: een andere constraint is een fout in de code of
    de database en moet doorgaan, zodat ze niet als "Dit lid bestaat niet meer." verdwijnt."""
    anna, _, bert = twee
    orig = mock.Mock(diag=mock.Mock(constraint_name="beheerder_rol_geldig"))
    fout = IntegrityError("UPDATE beheerder", {}, orig)
    with mock.patch.object(db.session, "commit", side_effect=fout), pytest.raises(IntegrityError):
        beheerders.lid_koppelen(bert.id, lid().id, actor(anna))
    assert lid_van(bert) is None


# Uitnodigen zonder lid (BV-96, variant 2B)


def test_uitnodigen_heeft_geen_lid_en_het_log_noemt_er_geen(app):
    with pytest.raises(TypeError):
        beheerders.uitnodigen("carla", "kijker", CLI, lid_id=1)
    beheerders.uitnodigen("carla", "kijker", CLI)
    carla = db.session.scalar(select(Beheerder))
    assert carla.lid_id is None
    [regel] = logregels("beheerder.uitgenodigd")
    assert "lid" not in regel.gegevens and regel.verwijzingen == [f"beheerder:{carla.id}"]


# Besluit 7: een kijker niet aan een oud-lid, een beheerder wel


def oud_lid(nummer="9", **velden):
    return lid(nummer, "Oud", **(velden or {"opzegdatum": vandaag()}))


@pytest.mark.parametrize("veld,dagen", [("opzegdatum", 0), ("opzegdatum", -9), ("uit_bron_op", 0)],
                         ids=["vandaag", "eerder", "uit_bron"])
def test_koppelen_van_een_kijker_aan_een_oud_lid_wordt_geweigerd(app, twee, veld, dagen):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    with pytest.raises(Regelfout, match=OUD):
        beheerders.lid_koppelen(bert.id, oud_lid(**{veld: datum(dagen)}).id, actor(anna))
    assert lid_van(bert) is None and not logregels("beheerder.lid_gewijzigd")


def test_een_gekoppeld_account_wordt_geen_kijker_als_het_lid_oud_is(app, twee):
    anna, _, bert = twee
    ld = lid("1", "Straks oud")
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    zeg_op(ld, vandaag())
    with pytest.raises(Regelfout, match=OUD_KIJKER):
        beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert rol_van(bert) == "beheerder" and not logregels("beheerder.rol_gewijzigd")


def test_een_beheerder_mag_aan_een_oud_lid_gekoppeld_worden_en_blijven(app, twee):
    anna, _, bert = twee
    ld = oud_lid()
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    beheerders.uitnodigen("carla", "beheerder", actor(anna))
    carla = db.session.scalar(select(Beheerder).where(Beheerder.gebruikersnaam == "carla"))
    beheerders.lid_koppelen(carla.id, ld.id, actor(anna))
    assert lid_van(bert) == lid_van(carla) == ld.id


def test_een_kijker_wordt_weer_beheerder_ook_als_zijn_lid_intussen_oud_lid_werd(app, twee):
    anna = twee[0]
    ld = lid("2", "Straks oud")
    beheerders.uitnodigen("dave", "kijker", actor(anna))
    dave = db.session.scalar(select(Beheerder).where(Beheerder.gebruikersnaam == "dave"))
    beheerders.lid_koppelen(dave.id, ld.id, actor(anna))
    zeg_op(ld, vandaag())
    beheerders.rol_wijzigen(dave.id, "beheerder", actor(anna))
    assert rol_van(dave) == "beheerder"


@pytest.mark.parametrize("dagen", [1, 30], ids=["morgen", "later"])
def test_een_kijker_aan_een_lid_dat_nog_niet_is_opgezegd_mag(app, twee, dagen):
    """Grens: een opzegdatum van morgen is nog geen oud-lid."""
    anna, _, bert = twee
    ld = lid(opzegdatum=vandaag() + timedelta(days=dagen))
    beheerders.lid_koppelen(bert.id, ld.id, actor(anna))
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert rol_van(bert) == "kijker"


def test_een_kijker_zonder_koppeling_wordt_zonder_controle_kijker(app, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert rol_van(bert) == "kijker"


# Racetest van de afgeleide regel: samen geen kijker aan een oud-lid. Het slot is dat van
# test_gebruikers_rollen: de tweede sessie wacht op de eerste (de assert in race) en ziet daarna de
# nieuwe waarden. `eerder` laadt het account zonder slot, zoals laad_beheerder, zodat een ontbrekende
# populate_existing een verouderde waarde zou geven.


def test_koppelen_aan_een_oud_lid_en_maak_kijker_tegelijk_geven_geen_kijker_aan_een_oud_lid_a(app, twee):
    """Eerst wordt de koppeling vastgelegd, daarna wil de tweede sessie het account kijker maken."""
    anna, _, bert = twee
    oud = oud_lid()

    def actie():
        eerder = db.session.get(Beheerder, bert.id)
        beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
        assert eerder is not None

    fouten = race(app, ["SELECT id FROM beheerder WHERE id = :b FOR UPDATE",
                        "UPDATE beheerder SET lid_id = :l WHERE id = :b"], {"b": bert.id, "l": oud.id}, actie)
    assert fouten == [OUD_KIJKER]
    assert rol_van(bert) == "beheerder" and lid_van(bert) == oud.id


def test_koppelen_aan_een_oud_lid_en_maak_kijker_tegelijk_geven_geen_kijker_aan_een_oud_lid_b(app, twee):
    """Eerst wordt het account kijker, daarna wil de tweede sessie het aan een oud-lid koppelen."""
    anna, _, bert = twee
    oud = oud_lid()

    def actie():
        eerder = db.session.get(Beheerder, bert.id)
        beheerders.lid_koppelen(bert.id, oud.id, actor(anna))
        assert eerder is not None

    fouten = race(app, ["SELECT id FROM beheerder WHERE id = :b FOR UPDATE",
                        "UPDATE beheerder SET rol = 'kijker' WHERE id = :b"], {"b": bert.id}, actie)
    assert fouten == [OUD]
    assert rol_van(bert) == "kijker" and lid_van(bert) is None


# Status (ADR-010)


def test_status_met_nul_een_en_meer_accounts(app, ingelogd):
    """Het ingelogde account (anna) is ongekoppeld. Nul: ok, 0 en een lege lijst; geblokkeerde accounts
    tellen mee; een beheerder met een lid dat nog lid is, staat er niet."""
    s = json_status(ingelogd)
    assert s["niet_gekoppeld"] == {"status": "waarschuwing", "aantal": 1, "gebruikers": ["anna"]}
    assert s["beheerders_oud_lid"] == {"status": "ok", "aantal": 0, "gebruikers": []}
    html = ingelogd.get("/status").get_data(as_text=True)
    assert "Gebruikers zonder lid" in html and "1: anna" in html and "Beheerders met een oud-lid" not in html

    actief, oud = lid("1", "Nog lid"), oud_lid()
    db.session.execute(text("UPDATE beheerder SET lid_id = :l WHERE gebruikersnaam = 'anna'"), {"l": actief.id})
    db.session.commit()
    s = json_status(ingelogd)
    assert s["niet_gekoppeld"] == {"status": "ok", "aantal": 0, "gebruikers": []}
    # BV-96: bij nul geen rij in de HTML; /status.json houdt de sleutels.
    html = ingelogd.get("/status").get_data(as_text=True)
    assert "Gebruikers zonder lid" not in html and "Beheerders met een oud-lid" not in html

    # Meer: twee beheerders met een oud-lid (een geblokkeerd), een kijker met een oud-lid hoort er niet in,
    # twee ongekoppelde accounts, gesorteerd.
    for naam, rol, actief_, lid_id in [("zoe", "beheerder", True, oud.id), ("bas", "beheerder", False, oud.id),
                                       ("kim", "kijker", True, oud.id), ("tom", "beheerder", True, None),
                                       ("eva", "kijker", False, None)]:
        db.session.execute(text("INSERT INTO beheerder (naam, gebruikersnaam, rol, actief, lid_id) "
                                "VALUES (:n, :n, :r, :a, :l)"), {"n": naam, "r": rol, "a": actief_, "l": lid_id})
    db.session.commit()
    s = json_status(ingelogd)
    assert s["beheerders_oud_lid"] == {"status": "waarschuwing", "aantal": 2, "gebruikers": ["bas", "zoe"]}
    assert s["niet_gekoppeld"] == {"status": "waarschuwing", "aantal": 2, "gebruikers": ["eva", "tom"]}
    html = ingelogd.get("/status").get_data(as_text=True)
    assert "Beheerders met een oud-lid" in html and "2: bas, zoe" in html and "2: eva, tom" in html


def test_status_beheerder_met_lid_dat_morgen_opzegt_is_geen_oud_lid(app, ingelogd):
    ld = lid(opzegdatum=morgen())
    db.session.execute(text("UPDATE beheerder SET lid_id = :l"), {"l": ld.id})
    db.session.commit()
    assert json_status(ingelogd)["beheerders_oud_lid"]["aantal"] == 0
    zeg_op(ld, vandaag())
    assert json_status(ingelogd)["beheerders_oud_lid"]["gebruikers"] == ["anna"]


def test_status_noemt_geen_lidgegevens(app, ingelogd):
    ld = lid("7788", "Geheimnaam Lid", opzegdatum=vandaag() - timedelta(days=3))
    db.session.execute(text("UPDATE beheerder SET lid_id = :l"), {"l": ld.id})
    db.session.commit()
    for pagina in (ingelogd.get("/status.json"), ingelogd.get("/status")):
        tekst = pagina.get_data(as_text=True)
        assert "anna" in tekst and "7788" not in tekst and "Geheimnaam" not in tekst
        assert (vandaag() - timedelta(days=3)).isoformat() not in tekst


# Migratie 0023


def kolomrechten(cfg, rol="botenloods_taken"):
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as c:
        rijen = c.execute(text(
            "SELECT column_name, privilege_type FROM information_schema.column_privileges "
            "WHERE table_name = 'beheerder' AND grantee = :r"), {"r": rol}).all()
        tabel = c.execute(text(
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE table_name = 'beheerder' AND grantee = :r"), {"r": rol}).scalars().all()
    engine.dispose()
    return {tuple(r) for r in rijen}, set(tabel)


def test_migratie_0023_upgrade_downgrade_upgrade_met_twee_accounts_aan_een_lid(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0022")
    assert kolomrechten(cfg) == (set(), set())
    command.upgrade(cfg, "0023")
    assert kolomrechten(cfg) == (
        {("id", "SELECT"), ("gebruikersnaam", "SELECT"), ("rol", "SELECT"), ("lid_id", "SELECT")}, {"DELETE"})
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.begin() as c:
        c.execute(text("INSERT INTO lid (lidnummer, naam) VALUES ('1', 'Een')"))
        c.execute(text("INSERT INTO beheerder (naam, gebruikersnaam, rol, lid_id) VALUES "
                       "('A', 'a', 'beheerder', 1), ('B', 'b', 'kijker', 1), ('C', 'c', 'beheerder', NULL)"))
    with engine.connect() as c:  # twee accounts aan een lid: geen uniciteit
        assert c.execute(text("SELECT count(*) FROM beheerder WHERE lid_id = 1")).scalar() == 2
    with engine.begin() as c:  # SET NULL
        c.execute(text("DELETE FROM lid"))
        assert c.execute(text("SELECT count(*) FROM beheerder WHERE lid_id IS NULL")).scalar() == 3
        c.execute(text("INSERT INTO lid (lidnummer, naam) VALUES ('2', 'Twee')"))
        c.execute(text("UPDATE beheerder SET lid_id = (SELECT id FROM lid) WHERE gebruikersnaam <> 'c'"))
    command.downgrade(cfg, "0022")
    assert kolomrechten(cfg) == (set(), set())
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM beheerder")).scalar() == 3
        with pytest.raises(ProgrammingError, match="lid_id"):
            c.execute(text("SELECT lid_id FROM beheerder"))
    command.upgrade(cfg, "head")
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM beheerder WHERE lid_id IS NULL")).scalar() == 3
    engine.dispose()


@pytest.mark.parametrize("sql", ["SELECT naam FROM beheerder", "SELECT wachtwoordhash FROM beheerder",
                                 "SELECT actief FROM beheerder", "UPDATE beheerder SET rol = 'kijker'",
                                 "INSERT INTO beheerder (naam, gebruikersnaam, rol) VALUES ('X', 'x', 'kijker')",
                                 "SELECT 1 FROM passkey", "SELECT 1 FROM token"])
@pytest.mark.worker
def test_de_worker_heeft_alleen_de_kolommen_en_het_delete_recht_van_0023(app, sql):
    with pytest.raises(ProgrammingError, match="permission denied"):
        db.session.execute(text(sql))
    db.session.rollback()


@pytest.mark.worker
def test_de_worker_leest_vier_kolommen_en_verwijdert(app):
    eigenaar("INSERT INTO beheerder (naam, gebruikersnaam, rol) VALUES ('X', 'x', 'kijker')")
    assert db.session.execute(text("SELECT id, gebruikersnaam, rol, lid_id FROM beheerder")).all()
    assert db.session.execute(text("DELETE FROM beheerder")).rowcount == 1
    db.session.rollback()
