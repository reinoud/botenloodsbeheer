"""Bewaartermijn van 5 jaar (BLB-026, ADR-006) en de dagelijkse opschoning in de worker (ADR-007).
De tests draaien als botenloods_taken, de rol van de worker; één test laat zien dat de webrol het
niet kan."""

import threading
from datetime import UTC, datetime, time, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import ProgrammingError

from app import create_app, taken
from app.domein import CLI, leden, log, opschonen, toewijzing, vandaag, wachtlijst
from app.models import Afbeelding, Boot, Lid, Logregel, Taakrun, Wachtlijst, db
from tests.unit.conftest import EIGENAAR, TAKEN, WEB
from tests.unit.hulp import als_api, lid, png
from tests.unit.test_indeling_en_toewijzing import boot, plaats
from tests.unit.test_leden import record
from tests.unit.test_tokens import eigenaar

pytestmark = pytest.mark.worker


def grens():
    return leden.jaren_terug(vandaag(), leden.BEWAARJAREN)


def tel(model):
    db.session.expire_all()
    return db.session.scalar(select(func.count()).select_from(model))


def bestaat(lid_id):
    db.session.expire_all()
    return db.session.get(Lid, lid_id) is not None


def opgezegd(dag, nummer="1001", veld="opzegdatum"):
    return lid(nummer, f"Lid {nummer}", **{veld: dag})


def foto_erbij(boot_id, sleutel):
    """De worker maakt geen foto's (#60); de eigenaar zet er een bij."""
    eigenaar("WITH a AS (INSERT INTO afbeelding (soort, mime_type, inhoud, breedte, hoogte, sleutel) "
             "VALUES ('foto', 'image/png', :inhoud, 40, 30, :sleutel) RETURNING id) "
             "UPDATE boot SET afbeelding_id = (SELECT id FROM a) WHERE id = :boot",
             inhoud=png(), sleutel=sleutel, boot=boot_id)


def zeg_op(lid_, dag):
    """Na het aanmaken van de boten: een oud-lid krijgt geen nieuwe boot (BLB-005)."""
    eigenaar("UPDATE lid SET opzegdatum = :d WHERE id = :i", d=dag, i=lid_.id)


# Oud-leden (criteria 1, 2 en 4)


def test_oud_lid_weg_met_boten_fotos_en_wachtlijst(app):
    """Criterium 1: ook een boot zonder plaats en een boot op de wachtlijst gaan mee."""
    weg = lid()
    eigen = boot(weg.id).id
    foto_erbij(eigen, "foto-weg")
    wachtlijst.erop_zetten(boot(weg.id, naam="Reiger").id, None, CLI)
    zeg_op(weg, grens() - timedelta(days=1))
    weg = weg.id
    blijft = lid("1002", "Bert").id
    foto_erbij(boot(blijft, naam="Fuut").id, "foto-blijft")

    assert opschonen.draai() == {"logregels": 0, "kijkers": 0, "leden": 1, "boten": 2, "fotos": 1, "imports": 0,
                                 "koppelingen": 0}
    assert not bestaat(weg) and bestaat(blijft)
    assert db.session.get(Boot, eigen) is None and tel(Boot) == 1
    assert tel(Afbeelding) == 1 and tel(Wachtlijst) == 0


@pytest.mark.parametrize("veld", ["opzegdatum", "uit_bron_op"])
def test_grens_precies_5_jaar_blijft_een_dag_eerder_weg(app, veld):
    """Grens: precies 5 jaar blijft (deze test, lid 2), een dag ouder gaat weg (lid 1). Zonder
    opzegdatum telt uit_bron_op (architectuur §9 besluit 4)."""
    weg = opgezegd(grens() - timedelta(days=1), "1", veld).id
    blijft = opgezegd(grens(), "2", veld).id
    opschonen.draai()
    assert not bestaat(weg) and bestaat(blijft)


def test_opzegdatum_gaat_voor_uit_bron_op(app):
    """Een recente opzegdatum houdt het lid, ook als het lang geleden uit de bron verdween."""
    blijft = lid("1", "Lid 1", opzegdatum=vandaag(), uit_bron_op=grens() - timedelta(days=400))
    opschonen.draai()
    assert bestaat(blijft.id)


def test_boot_met_plaats_houdt_het_oud_lid_met_al_zijn_boten(app):
    """Criterium 2; een boot zonder plaats houdt het opschonen niet tegen (criterium 1)."""
    oud = lid("1", "Lid 1")
    op_plaats = boot(oud.id)
    zonder = boot(oud.id, naam="Reiger")
    toewijzing.toewijzen(plaats().id, op_plaats.id, CLI)
    zeg_op(oud, grens() - timedelta(days=1))
    opschonen.draai()
    assert bestaat(oud.id) and db.session.get(Boot, zonder.id) is not None


@pytest.mark.parametrize("dagen", [None, 30], ids=["lid", "gaat_opzeggen"])
def test_lid_blijft_altijd(app, dagen):
    """Criterium 4."""
    blijft = lid("1", "Lid 1", opzegdatum=dagen and vandaag() + timedelta(days=dagen))
    boot(blijft.id)
    opschonen.draai()
    assert bestaat(blijft.id) and tel(Boot) == 1


# Log (criteria 3 en 5)


def test_logregel_ouder_dan_5_jaar_weg_jonger_blijft(app):
    """Criterium 3. Grens: een minuut ouder dan 5 jaar weg, een minuut jonger blijft."""
    vijf = leden.jaren_terug(datetime.now(UTC), leden.BEWAARJAREN)
    for minuten, naam in ((-1, "oud"), (1, "jong")):
        db.session.add(Logregel(tijdstip=vijf + timedelta(minutes=minuten), soort="mutatie",
                                actor_soort="systeem", actor_naam=naam, actie="boot.aangemaakt"))
    db.session.commit()
    assert opschonen.draai()["logregels"] == 1
    namen = db.session.scalars(select(Logregel.actor_naam)).all()
    assert "jong" in namen and "oud" not in namen


def test_uitkomst_in_taakrun_en_technisch_log_zonder_persoonsgegevens(app):
    """Criterium 5; ADR-006: na het opschonen staat het lid in jongere logregels alleen als
    `lid:<id>`, zonder naam."""
    weg = lid("1001", "Lid 1001")
    wachtlijst.erop_zetten(boot(weg.id, naam="Zeemeeuw").id, None, CLI)
    zeg_op(weg, grens() - timedelta(days=1))
    weg = weg.id
    opschonen.draai()
    [run] = db.session.scalars(select(Taakrun).where(Taakrun.taak == opschonen.TAAK)).all()
    assert (run.status, run.aantallen) == ("geslaagd",
                                           {"logregels": 0, "kijkers": 0, "leden": 1, "boten": 1, "fotos": 0,
                                                "imports": 0, "koppelingen": 0})
    [r] = log.regels(technisch=True, acties=("opschoning.",))
    assert (r.actor_naam, r.verwijzingen, r.gegevens) == (
        "opschoning", [f"taakrun:{run.id}"], run.aantallen)
    alles = " ".join(str((r.gegevens, r.verwijzingen)) for r in db.session.scalars(select(Logregel)))
    assert f"lid:{weg}" in alles and "Lid 1001" not in alles


def test_opgeschoond_oud_lid_komt_niet_terug_via_de_import(app):
    """Architectuur §10 risico 1, ADR-004 stap 4: de bron levert het oud-lid nog."""
    opgezegd(grens() - timedelta(days=1), "1")
    opgezegd(vandaag(), "2")
    opschonen.draai()
    als_api(leden.importeer, [record("1", opzegdatum=(grens() - timedelta(days=1)).isoformat()),
                              record("2", opzegdatum=vandaag().isoformat())], CLI)
    db.session.expire_all()
    assert db.session.scalars(select(Lid.lidnummer)).all() == ["2"]


def test_gelijktijdig_toewijzen_en_opschonen_faalt_veilig(app):
    """ADR-006, #298: het oud-lid valt vandaag nog binnen de termijn (toewijzen mag) en morgen erbuiten
    (de opschoning van morgen kiest het). De toewijzing houdt het slot op de boot; de DELETE van de opschoning
    wacht en raakt daarna een boot met een plaats. `plaats.boot_id` heeft geen ON DELETE, dus de database
    weigert: de hele opschoning rolt terug, het oud-lid en zijn boot blijven en de run staat als mislukt.
    Mutant: ON DELETE CASCADE of SET NULL op plaats.boot_id zou de plaats of de boot stil weghalen; die
    migratie is niet gemuteerd."""
    oud = opgezegd(grens())
    b = boot(oud.id)
    p = plaats()
    morgen = vandaag() + timedelta(days=1)
    uitkomst = []

    def opschonen_morgen():
        with app.app_context():
            try:
                opschonen.draai(morgen)
            except Exception as fout:  # noqa: BLE001 (de thread meldt elke fout aan de test)
                uitkomst.append(type(fout).__name__)

    engine = create_engine(WEB)
    with engine.connect() as toewijzen:
        toewijzen.execute(text("SELECT id FROM boot WHERE id = :b FOR UPDATE"), {"b": b.id})
        draad = threading.Thread(target=opschonen_morgen)
        draad.start()
        draad.join(timeout=2)
        assert draad.is_alive(), "de opschoning wacht niet op het slot van de toewijzing"
        toewijzen.execute(text("UPDATE plaats SET boot_id = :b WHERE id = :p"), {"b": b.id, "p": p.id})
        toewijzen.commit()
    draad.join(timeout=10)
    engine.dispose()
    db.session.expire_all()
    assert uitkomst == ["IntegrityError"]
    assert bestaat(oud.id) and db.session.get(Boot, b.id).plaats.id == p.id
    assert runs() == ["mislukt"]


# Kijkers met een oud-lid (ADR-015, #353)


def account(naam, rol="kijker", lid_=None, actief=True):
    """Zet een account neer als eigenaar: de worker maakt er geen aan en leest er vier kolommen van."""
    eigenaar("INSERT INTO beheerder (naam, gebruikersnaam, rol, actief, lid_id) VALUES (:n, :n, :r, :a, :l)",
             n=naam, r=rol, a=actief, l=lid_ and lid_.id)


def accounts():
    """Gebruikersnaam, rol en lid_id van elk account, met de kolommen die de worker mag lezen."""
    db.session.rollback()
    return {n: (r, lid_id) for n, r, lid_id in db.session.execute(text(
        "SELECT gebruikersnaam, rol, lid_id FROM beheerder"))}


def test_kijker_met_een_oud_lid_gaat_weg_de_rest_blijft(app):
    """Besluiten 1 en 6: weg is alleen een kijker met een gekoppeld oud-lid. Een kijker met een lid, een kijker
    zonder koppeling en een beheerder met een oud-lid blijven; het oud-lid zelf blijft binnen de termijn."""
    oud, actief = opgezegd(vandaag() - timedelta(days=3), "1"), lid("2", "Nog lid")
    account("kijker_oud", lid_=oud)
    account("kijker_actief", lid_=actief)
    account("kijker_los")
    account("beheerder_oud", "beheerder", oud)
    aantallen = opschonen.draai()
    assert aantallen["kijkers"] == 1 and aantallen["leden"] == 0
    assert accounts() == {"kijker_actief": ("kijker", actief.id), "kijker_los": ("kijker", None),
                          "beheerder_oud": ("beheerder", oud.id)}
    assert bestaat(oud.id)


@pytest.mark.parametrize("dagen,weg", [(-1, True), (0, True), (1, False)], ids=["gisteren", "vandaag", "morgen"])
@pytest.mark.parametrize("veld", ["opzegdatum", "uit_bron_op"])
def test_grens_van_het_oud_lid_voor_de_kijker(app, veld, dagen, weg):
    """Dezelfde regel als is_oud_lid: vandaag is al oud-lid, morgen nog niet."""
    account("kijker", lid_=opgezegd(vandaag() + timedelta(days=dagen), "1", veld))
    assert opschonen.draai()["kijkers"] == int(weg)
    assert ("kijker" in accounts()) is not weg


def test_een_geblokkeerde_kijker_gaat_ook_weg(app):
    account("kijker", lid_=opgezegd(vandaag(), "1"), actief=False)
    assert opschonen.draai()["kijkers"] == 1 and accounts() == {}


def test_de_opschoning_van_een_kijker_krijgt_een_logregel_zonder_lidgegevens(app):
    oud = opgezegd(vandaag(), "1")
    account("kijker", lid_=oud)
    kijker_id = db.session.scalar(text("SELECT id FROM beheerder"))
    db.session.rollback()
    opschonen.draai()
    [regel] = log.regels(technisch=True, acties=("beheerder.",))
    assert (regel.actie, regel.actor_soort, regel.actor_naam) == ("beheerder.verwijderd", "taak", "opschoning")
    assert regel.verwijzingen == [f"beheerder:{kijker_id}", f"lid:{oud.id}"]
    assert regel.gegevens == {"gebruikersnaam": "kijker", "reden": "oud-lid"}


def test_een_kijker_gaat_weg_voor_zijn_lid_dat_in_dezelfde_run_wordt_opgeschoond(app):
    """Volgorde: na het verwijderen van het lid had SET NULL de koppeling al gewist en bleef de kijker staan.
    Een beheerder aan dat lid blijft, zonder koppeling (besluit 5)."""
    oud = opgezegd(grens() - timedelta(days=1), "1")
    account("kijker", lid_=oud)
    account("beheerder", "beheerder", oud)
    oud = oud.id
    aantallen = opschonen.draai()
    assert (aantallen["kijkers"], aantallen["leden"]) == (1, 1)
    assert not bestaat(oud)
    assert accounts() == {"beheerder": ("beheerder", None)}


def test_passkeys_uitnodigingen_en_tokens_van_de_kijker_gaan_mee(app):
    """De cascades draaien met de rechten van de eigenaar van de tabellen: de worker heeft ze zelf niet."""
    account("kijker", lid_=opgezegd(vandaag(), "1"))
    eigenaar("INSERT INTO passkey (beheerder_id, credential_id, publieke_sleutel, teller, naam) "
             "SELECT id, 'c', 'k', 0, 'toestel' FROM beheerder")
    eigenaar("INSERT INTO uitnodiging (beheerder_id, code_hash, verloopt_op) SELECT id, 'h', now() FROM beheerder")
    eigenaar("INSERT INTO token (naam, soort, prefix, hash, rechten, verloopt_op, beheerder_id, gemaakt_door) "
             "SELECT 'pers', 'persoonlijk', 'blb_abcd', 'h', ARRAY['leden:lezen'], now(), id, 'test' FROM beheerder")
    opschonen.draai()
    for tabel in ("beheerder", "passkey", "uitnodiging", "token"):
        assert eigenaar_telt(tabel) == 0, tabel


def eigenaar_telt(tabel):
    engine = create_engine(EIGENAAR)
    with engine.connect() as c:
        n = c.execute(text(f"SELECT count(*) FROM {tabel}")).scalar()
    engine.dispose()
    return n


def test_zonder_kijkers_met_een_oud_lid_blijft_alles_en_staat_kijkers_op_nul(app):
    account("kijker")
    assert opschonen.draai()["kijkers"] == 0 and len(accounts()) == 1


# Planning in de worker (ADR-007)


def runs():
    db.session.expire_all()
    return db.session.scalars(select(Taakrun.status).where(Taakrun.taak == opschonen.TAAK)
                              .order_by(Taakrun.id)).all()


def test_een_keer_per_dag(app):
    assert opschonen.draai() is not None
    assert opschonen.draai() is None and runs() == ["geslaagd"]
    assert opschonen.draai(vandaag() + timedelta(days=1)) is not None


def test_na_een_fout_pas_de_volgende_dag_opnieuw(app):
    opgezegd(grens() - timedelta(days=1))
    with (mock.patch.object(opschonen, "opschonen", side_effect=RuntimeError("geheim-123")),
          pytest.raises(RuntimeError)):
        opschonen.draai()
    assert runs() == ["mislukt"]
    [melding] = db.session.scalars(select(Taakrun.foutmelding)).all()
    assert melding.startswith("RuntimeError") and "geheim-123" not in melding
    assert tel(Lid) == 1  # niets half verwijderd
    assert opschonen.draai() is None and runs() == ["mislukt"]
    assert opschonen.draai(vandaag() + timedelta(days=1))["leden"] == 1


def test_nooit_twee_tegelijk(app):
    """De advisory lock van een tweede worker (ADR-007, stap 3)."""
    engine = create_engine(TAKEN)
    with engine.connect() as ander:
        ander.execute(text("SELECT pg_advisory_lock(:s)"), {"s": opschonen.SLOT})
        assert opschonen.draai() is None and runs() == []
    engine.dispose()
    assert opschonen.draai() is not None


def test_niet_tijdens_een_import_die_het_oud_lid_weer_actief_maakt(app):
    """#49: de import houdt het importslot; de opschoning wacht een ronde en het lid blijft."""
    oud = lid()
    boot(oud.id)
    zeg_op(oud, grens() - timedelta(days=1))
    engine = create_engine(TAKEN)
    with engine.connect() as import_:
        import_.execute(text("SELECT pg_advisory_lock(:s)"), {"s": leden.IMPORT_SLOT})
        assert opschonen.draai() is None and runs() == []
        assert bestaat(oud.id) and tel(Boot) == 1
        eigenaar("UPDATE lid SET opzegdatum = NULL WHERE id = :i", i=oud.id)  # weer in de bron
        import_.execute(text("SELECT pg_advisory_unlock(:s)"), {"s": leden.IMPORT_SLOT})
    engine.dispose()
    assert opschonen.draai()["leden"] == 0
    assert bestaat(oud.id) and tel(Boot) == 1


def test_ronde_na_de_opschoning_neemt_geen_slot(app):
    """#346: anders krijgt een import in dat venster een 409."""
    assert opschonen.draai() is not None
    sloten = []
    echt = opschonen.gedraaid_op

    def spion(dag):
        sloten.append(db.session.scalar(text(
            "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND pid = pg_backend_pid()")))
        return echt(dag)

    with mock.patch.object(opschonen, "gedraaid_op", spion):
        taken.ronde(datetime.combine(vandaag(), time(23, 0), ZoneInfo(app.config["TZ"])))
    assert sloten == [0] and runs() == ["geslaagd"]


@pytest.mark.parametrize("uur,minuut,gedraaid", [(3, 59, False), (4, 0, True)],
                         ids=["voor_het_tijdstip", "op_het_tijdstip"])
def test_ronde_draait_de_opschoning_vanaf_het_tijdstip(app, uur, minuut, gedraaid):
    """Grens van OPSCHOON_TIJDSTIP (standaard 04:00), in de tijdzone van de installatie."""
    tz = ZoneInfo(app.config["TZ"])
    taken.ronde(datetime.combine(vandaag(), time(uur, minuut), tz))
    assert runs() == (["geslaagd"] if gedraaid else [])


@pytest.mark.parametrize("waarde,verwacht", [("05:30", time(5, 30)), (None, time(4, 0))],
                         ids=["ingesteld", "standaard"])
def test_opschoon_tijdstip_uit_de_omgeving(monkeypatch, waarde, verwacht):
    if waarde:
        monkeypatch.setenv("OPSCHOON_TIJDSTIP", waarde)
    monkeypatch.setenv("DIENST", "worker")
    assert create_app({"TESTING": True}).config["OPSCHOON_TIJDSTIP"] == verwacht


@pytest.mark.parametrize("waarde", ["4 uur", "25:00", ""], ids=["tekst", "buiten_bereik", "leeg"])
def test_ongeldig_opschoon_tijdstip_stopt_het_starten(monkeypatch, waarde):
    from app.config import ConfigFout

    monkeypatch.setenv("OPSCHOON_TIJDSTIP", waarde)
    with pytest.raises(ConfigFout, match="OPSCHOON_TIJDSTIP"):
        create_app({"TESTING": True})


def test_webrol_mag_niet_opschonen(database):
    """ADR-006: alleen de rol van de worker mag logregels verwijderen. Zonder de fixture app,
    dus als botenloods_web uit DATABASE_URL."""
    web = create_app({"TESTING": True})
    with web.app_context():
        with pytest.raises(ProgrammingError, match="permission denied"):
            opschonen.draai()
        assert db.session.scalars(select(Taakrun.status)).all() == ["mislukt"]
        db.session.remove()
        db.engine.dispose()
    with database.begin() as c:
        c.execute(text("TRUNCATE taakrun RESTART IDENTITY"))
