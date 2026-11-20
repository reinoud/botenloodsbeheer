"""Rollen per account (BLB-050, ADR-015, issue #322): uitnodigen met een rol, de rol wijzigen met de
vergrendeling op de laatste beheerder, de tokens die met de rol vervallen, het scherm Gebruikers en de
migratie 0022 (kolom, check, recht voor api en de downgrade met een kijker)."""

import time

import pytest
from alembic import command
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.domein import CLI, Actor, Regelfout, beheerders, log
from app.models import Beheerder, Token, db
from tests.unit.conftest import API, EIGENAAR, nieuwe_database
from tests.unit.hulp import beheerder_met_wachtwoord, race
from tests.unit.test_beheerders_beheren import logacties, met_passkey
from tests.unit.test_persoonlijke_tokens import boten, logregels, persoonlijk
from tests.unit.test_tokens import app_uit_omgeving
from tests.unit.test_web import inloggen


def actor(b):
    return Actor.van(b)


@pytest.fixture
def twee():
    """(anna, geheim van anna, bert): twee actieve beheerders met wachtwoord en TOTP."""
    anna, geheim = beheerder_met_wachtwoord("anna")
    bert, _ = beheerder_met_wachtwoord("bert")
    return anna, geheim, bert


@pytest.fixture
def api_client(app, monkeypatch):
    return app_uit_omgeving(monkeypatch, DIENST="api").test_client()


def rol_van(b):
    db.session.expire_all()
    return db.session.get(Beheerder, b.id).rol


# Uitnodigen met een rol


@pytest.mark.parametrize("rol", ["beheerder", "kijker"])
def test_uitnodigen_legt_de_rol_vast_en_logt_hem(app, rol):
    beheerders.uitnodigen("carla", rol, CLI)
    carla = db.session.scalar(select(Beheerder))
    assert carla.rol == rol
    [regel] = logregels("beheerder.uitgenodigd")
    assert regel.gegevens["rol"] == rol and regel.gegevens["gebruikersnaam"] == "carla"


@pytest.mark.parametrize("rol", ["", "admin", "Beheerder", None], ids=["leeg", "onbekend", "hoofdletter", "none"])
def test_uitnodigen_weigert_een_ontbrekende_of_onbekende_rol(app, rol):
    with pytest.raises(Regelfout, match="Kies een rol"):
        beheerders.uitnodigen("carla", rol, CLI)
    assert db.session.scalar(select(Beheerder)) is None


def test_de_database_weigert_een_onbekende_rol_en_een_ontbrekende_rol(app):
    """Model en migratie: de check rol_geldig en NOT NULL zonder standaardwaarde."""
    db.session.add(Beheerder(naam="x", gebruikersnaam="xx", rol="admin"))
    with pytest.raises(IntegrityError, match="rol_geldig"):
        db.session.commit()
    db.session.rollback()
    db.session.add(Beheerder(naam="x", gebruikersnaam="xx"))
    with pytest.raises(IntegrityError, match="null value"):
        db.session.commit()
    db.session.rollback()


# De rol wijzigen


def test_een_beheerder_maakt_een_collega_kijker_en_terug_met_een_logregel_per_wijziging(app, twee):
    anna, _, bert = twee
    assert beheerders.rol_wijzigen(bert.id, "kijker", actor(anna)) == "bert"
    assert rol_van(bert) == "kijker"
    beheerders.rol_wijzigen(bert.id, "beheerder", actor(anna))
    assert rol_van(bert) == "beheerder"
    regels = logregels("beheerder.rol_gewijzigd")
    assert [r.gegevens for r in regels] == [{"gebruikersnaam": "bert", "rol": ["beheerder", "kijker"]},
                                            {"gebruikersnaam": "bert", "rol": ["kijker", "beheerder"]}]
    assert regels[0].actor_naam == "anna" and regels[0].verwijzingen == [f"beheerder:{bert.id}"]


def test_dezelfde_rol_geeft_geen_logregel_en_wijzigt_niets(app, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "beheerder", actor(anna))
    assert logregels("beheerder.rol_gewijzigd") == [] and rol_van(bert) == "beheerder"


def test_een_beheerder_maakt_zichzelf_kijker_als_er_een_andere_beheerder_blijft(app, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(anna.id, "kijker", actor(anna))
    assert rol_van(anna) == "kijker" and rol_van(bert) == "beheerder"


def test_de_laatste_beheerder_wordt_geen_kijker(app, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    with pytest.raises(Regelfout, match="Er blijft geen beheerder over die kan inloggen. De rol van anna is niet gewijzigd."):
        beheerders.rol_wijzigen(anna.id, "kijker", actor(anna))
    assert rol_van(anna) == "beheerder" and len(logregels("beheerder.rol_gewijzigd")) == 1


def test_een_geblokkeerde_beheerder_telt_niet_mee_als_overblijvende_beheerder(app, twee):
    anna, _, bert = twee
    beheerders.blokkeren(bert.id, actor(anna))
    with pytest.raises(Regelfout, match="Er blijft geen beheerder over"):
        beheerders.rol_wijzigen(anna.id, "kijker", actor(anna))


def test_een_beheerder_zonder_inlogmethode_telt_niet_mee(app, twee):
    """#348: carla heeft haar uitnodiging nog niet gebruikt; anna wordt geen kijker, en niets verandert."""
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    beheerders.uitnodigen("carla", "beheerder", CLI)
    persoonlijk(anna)
    voor = logacties()
    with pytest.raises(Regelfout, match="Er blijft geen beheerder over die kan inloggen. De rol van anna is niet gewijzigd."):
        beheerders.rol_wijzigen(anna.id, "kijker", actor(anna))
    assert rol_van(anna) == "beheerder" and logacties() == voor
    assert db.session.scalar(select(Token)).ingetrokken_op is None


@pytest.mark.parametrize("methode", ["passkey", "wachtwoord"])
def test_een_beheerder_met_alleen_een_passkey_of_een_wachtwoord_telt_mee(app, twee, methode):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    if methode == "passkey":
        code = beheerders.uitnodigen("carla", "beheerder", CLI)
        carla = db.session.scalar(select(Beheerder).where(Beheerder.gebruikersnaam == "carla"))
        met_passkey(carla)
        assert code and carla.wachtwoordhash is None
    else:
        carla = beheerder_met_wachtwoord("carla")[0]
        assert not carla.passkeys
    beheerders.rol_wijzigen(anna.id, "kijker", actor(anna))
    assert rol_van(anna) == "kijker"


def test_een_kijker_telt_niet_mee_als_overblijvende_beheerder(app, twee):
    anna, _, bert = twee
    carla = beheerder_met_wachtwoord("carla", "kijker")[0]
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    with pytest.raises(Regelfout, match="Er blijft geen beheerder over"):
        beheerders.rol_wijzigen(anna.id, "kijker", actor(anna))
    assert rol_van(carla) == "kijker"


def test_een_geblokkeerd_account_wordt_kijker_zonder_dat_de_actor_wegvalt(app, twee):
    anna, _, bert = twee
    beheerders.blokkeren(bert.id, actor(anna))
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert rol_van(bert) == "kijker"


def test_een_kijker_wijzigt_geen_rollen(app, twee):
    anna, _, _ = twee
    kees = beheerder_met_wachtwoord("kees", "kijker")[0]
    with pytest.raises(Regelfout, match="Alleen een beheerder"):
        beheerders.rol_wijzigen(anna.id, "kijker", actor(kees))
    with pytest.raises(Regelfout, match="Alleen een beheerder"):
        beheerders.rol_wijzigen(kees.id, "beheerder", actor(kees))  # ook niet zichzelf omhoog
    assert rol_van(kees) == "kijker" and rol_van(anna) == "beheerder"


@pytest.mark.parametrize("functie", ["blokkeren", "deblokkeren", "verwijderen", "herstellen"])
def test_een_kijker_beheert_geen_accounts(app, twee, functie):
    _, _, bert = twee
    kees = beheerder_met_wachtwoord("kees", "kijker")[0]
    with pytest.raises(Regelfout, match="Alleen een beheerder"):
        getattr(beheerders, functie)(bert.id, actor(kees))
    assert db.session.get(Beheerder, bert.id) is not None


def test_een_geblokkeerde_actor_wijzigt_geen_rol(app, twee):
    anna, _, bert = twee
    beheerders.blokkeren(bert.id, actor(anna))
    with pytest.raises(Regelfout, match="niet meer actief"):
        beheerders.rol_wijzigen(anna.id, "kijker", actor(bert))


@pytest.mark.parametrize("rol", ["", "admin", "Kijker"])
def test_rol_wijzigen_weigert_een_onbekende_rol(app, twee, rol):
    anna, _, bert = twee
    with pytest.raises(Regelfout, match="Kies een rol"):
        beheerders.rol_wijzigen(bert.id, rol, actor(anna))


def test_rol_wijzigen_van_een_onbekend_account(app, twee):
    with pytest.raises(Regelfout, match="bestaat niet"):
        beheerders.rol_wijzigen(9999, "kijker", actor(twee[0]))


def test_de_sessieversie_blijft_bij_een_rolwijziging(app, twee):
    """De rol geldt vanaf het volgende verzoek; sessies eindigen niet (ADR-015)."""
    anna, _, bert = twee
    versie = bert.sessieversie
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert db.session.get(Beheerder, bert.id).sessieversie == versie


# Tokens


def test_een_kijker_wordt_gemaakt_met_intrekking_van_al_zijn_persoonlijke_tokens(app, twee):
    anna, _, bert = twee
    persoonlijk(bert, "bert-laptop")
    persoonlijk(bert, "bert-telefoon")
    persoonlijk(anna, "anna-laptop")
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    db.session.expire_all()
    ingetrokken = {t.naam: t.ingetrokken_op is not None for t in db.session.scalars(select(Token))}
    assert ingetrokken == {"bert-laptop": True, "bert-telefoon": True, "anna-laptop": False}
    regels = logregels("token.ingetrokken")
    assert sorted(r.gegevens["naam"] for r in regels) == ["bert-laptop", "bert-telefoon"]
    assert all(r.actor_naam == "anna" for r in regels)


def test_een_al_ingetrokken_token_krijgt_geen_tweede_logregel(app, twee):
    anna, _, bert = twee
    persoonlijk(bert, "bert-laptop")
    tokens_id = db.session.scalar(select(Token.id))
    from app.domein import tokens
    tokens.intrekken(tokens_id, actor(anna))
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert len(logregels("token.ingetrokken")) == 1


def test_een_robottoken_blijft_werken_als_zijn_maker_kijker_wordt(app, twee):
    anna, _, bert = twee
    from app.domein import tokens
    tokens.maken("robot", "koppeling", ["boten:lezen"], ["10.203.0.0/24"], None, actor(bert))
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert db.session.scalar(select(Token.ingetrokken_op)) is None


def test_terug_naar_beheerder_brengt_de_tokens_niet_terug(app, twee):
    anna, _, bert = twee
    persoonlijk(bert, "bert-laptop")
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    beheerders.rol_wijzigen(bert.id, "beheerder", actor(anna))
    db.session.expire_all()
    assert db.session.scalar(select(Token.ingetrokken_op)) is not None


def test_naar_beheerder_trekt_geen_tokens_in(app, twee):
    """Alleen kijker worden trekt tokens in. Een kijker heeft er normaal geen; deze maakt er een via het domein."""
    anna, _, _ = twee
    kees = beheerder_met_wachtwoord("kees", "kijker")[0]
    persoonlijk(kees, "kees-laptop")
    token_id = db.session.scalar(select(Token.id))
    beheerders.rol_wijzigen(kees.id, "beheerder", actor(anna))
    db.session.expire_all()
    assert db.session.get(Token, token_id).ingetrokken_op is None and logregels("token.ingetrokken") == []


def test_een_token_van_een_eigenaar_die_geen_beheerder_is_wordt_geweigerd(app, api_client, twee):
    """ADR-015: de controle per aanroep eist een actieve beheerder, ook voor een token dat tijdens de
    rolwijziging nog ontstond. Eerst de rol als eigenaar van de tabel, zonder de intrekking."""
    _, _, bert = twee
    waarde = persoonlijk(bert, "bert-laptop")
    assert boten(api_client, waarde).status_code == 200
    eigenaar = create_engine(EIGENAAR)
    with eigenaar.begin() as c:
        c.execute(text("UPDATE beheerder SET rol = 'kijker' WHERE id = :b"), {"b": bert.id})
    eigenaar.dispose()
    r = boten(api_client, waarde)
    assert (r.status_code, r.json) == (401, {"fout": "Geen toegang."})
    [regel] = logregels("api.geweigerd")
    assert regel.gegevens["reden"] == "eigenaar_inactief"


def test_een_token_van_een_beheerder_werkt_nog(app, api_client, twee):
    waarde = persoonlijk(twee[2], "bert-laptop")
    assert boten(api_client, waarde).status_code == 200


# Races (ADR-015): de vergrendeling op alle actieve accounts


def test_twee_beheerders_maken_elkaar_tegelijk_kijker(app, twee):
    """Anna maakt bert kijker terwijl bert anna kijker maakt. De eerste sessie vergrendelt bert en wijzigt
    hem; de tweede moet wachten, ziet dat bert kijker is en weigert. Zonder FOR UPDATE op de actieve
    accounts wacht hij niet (de assert in race), en zonder populate_existing ziet hij de oude rol."""
    anna, _, bert = twee

    def actie():
        eerder = db.session.get(Beheerder, bert.id)  # zoals laad_beheerder, zonder slot
        beheerders.rol_wijzigen(anna.id, "kijker", actor(bert))
        assert eerder is not None  # vast tot na de aanroep, zodat de identity map hem niet opruimt

    fouten = race(app, ["SELECT id FROM beheerder WHERE id = :b FOR UPDATE",
                        "UPDATE beheerder SET rol = 'kijker' WHERE id = :b"], {"b": bert.id}, actie)
    assert fouten == ["Alleen een beheerder wijzigt gebruikers."]
    assert rol_van(anna) == "beheerder" and rol_van(bert) == "kijker"


def test_twee_beheerders_maken_zichzelf_tegelijk_kijker(app, twee):
    """Anna en bert maken zichzelf kijker. Onder het slot ziet de tweede dat anna al kijker is en dat er
    dan geen beheerder overblijft."""
    anna, _, bert = twee
    fouten = race(app, ["SELECT id FROM beheerder WHERE id = :b FOR UPDATE",
                        "UPDATE beheerder SET rol = 'kijker' WHERE id = :b"], {"b": anna.id},
                  lambda: beheerders.rol_wijzigen(bert.id, "kijker", actor(bert)))
    assert fouten == ["Er blijft geen beheerder over die kan inloggen. De rol van bert is niet gewijzigd."]
    assert rol_van(anna) == "kijker" and rol_van(bert) == "beheerder"


def test_een_kijker_die_net_kijker_werd_blokkeert_niemand_meer(app, twee):
    """Blokkeren, deblokkeren, verwijderen en herstellen nemen hetzelfde slot en zien de nieuwe rol."""
    anna, _, bert = twee
    for functie in ("blokkeren", "verwijderen", "herstellen"):
        fouten = race(app, ["SELECT id FROM beheerder WHERE id = :b FOR UPDATE",
                            "UPDATE beheerder SET rol = 'kijker' WHERE id = :b"], {"b": bert.id},
                      lambda f=functie: getattr(beheerders, f)(anna.id, actor(bert)))
        assert fouten == ["Alleen een beheerder wijzigt gebruikers."], functie
        db.session.execute(text("UPDATE beheerder SET rol = 'beheerder'"))
        db.session.commit()


# Het scherm Gebruikers


@pytest.fixture
def scherm(client, twee):
    inloggen(client, twee[1])
    return client


def test_uitnodigen_via_het_scherm_vraagt_een_rol(scherm):
    r = scherm.post("/gebruikers", data={"gebruikersnaam": "carla"}, follow_redirects=True)
    assert "Kies een rol: beheerder of kijker." in r.text
    assert db.session.scalar(select(Beheerder).where(Beheerder.gebruikersnaam == "carla")) is None


def test_uitnodigen_via_het_scherm_maakt_een_kijker_en_noemt_hem_gebruiker(scherm):
    r = scherm.post("/gebruikers", data={"gebruikersnaam": "carla", "rol": "kijker"})
    assert r.status_code == 200 and "Gebruiker uitgenodigd" in r.text and "nieuwe gebruiker" in r.text
    assert db.session.scalar(select(Beheerder.rol).where(Beheerder.gebruikersnaam == "carla")) == "kijker"


def test_de_rolroute_zet_een_collega_om_en_meldt_de_tokens(scherm, twee):
    _, _, bert = twee
    r = scherm.post(f"/gebruikers/{bert.id}/rol", data={"rol": "kijker"}, follow_redirects=True)
    assert "bert is nu kijker. De persoonlijke tokens van bert zijn ingetrokken." in r.text
    r = scherm.post(f"/gebruikers/{bert.id}/rol", data={"rol": "beheerder"}, follow_redirects=True)
    assert "bert is nu beheerder." in r.text and "tokens van bert" not in r.text


def test_een_beheerder_die_zichzelf_kijker_maakt_landt_op_rekoverzicht_met_een_melding(scherm, twee):
    anna, _, _ = twee
    r = scherm.post(f"/gebruikers/{anna.id}/rol", data={"rol": "kijker"})
    assert r.status_code == 302 and r.location == "/rekoverzicht"
    tekst = scherm.get("/rekoverzicht").text
    assert tekst.count("Je bent nu kijker") == 1 and "Gebruikers kun je niet meer openen" in tekst
    assert "Je bent nu kijker: je ziet de loods en wijzigt niets. Je persoonlijke tokens zijn ingetrokken." in tekst
    assert scherm.get("/gebruikers").status_code == 403
    assert "Je bent nu kijker" not in scherm.get("/rekoverzicht").text  # de melding is eenmalig


def test_de_laatste_beheerder_kijker_maken_geeft_een_foutmelding_en_wijzigt_niets(scherm, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    r = scherm.post(f"/gebruikers/{anna.id}/rol", data={"rol": "kijker"}, follow_redirects=True)
    assert "Er blijft geen beheerder over die kan inloggen. De rol van anna is niet gewijzigd." in r.text
    assert 'ds-notice--danger' in r.text and rol_van(anna) == "beheerder"
    assert r.request.path == "/gebruikers"


def test_de_rolroute_vraagt_een_recente_inlog_ook_voor_het_eigen_account(scherm, twee):
    anna, _, bert = twee
    for doel in (bert, anna):
        with scherm.session_transaction() as s:  # een sessie van 11 minuten oud
            s.update(beheerder_id=anna.id, sessieversie=anna.sessieversie, ingelogd_op=int(time.time()) - 11 * 60)
        r = scherm.post(f"/gebruikers/{doel.id}/rol", data={"rol": "kijker"})
        assert r.status_code == 302 and r.location.startswith("/inloggen")
        with scherm.session_transaction() as s:
            assert "beheerder_id" not in s
    assert rol_van(bert) == "beheerder" and rol_van(anna) == "beheerder"


def test_de_rolroute_weigert_een_onbekende_rol_en_een_onbekend_account(scherm, twee):
    _, _, bert = twee
    r = scherm.post(f"/gebruikers/{bert.id}/rol", data={"rol": "admin"}, follow_redirects=True)
    assert "Kies een rol" in r.text and rol_van(bert) == "beheerder"
    r = scherm.post("/gebruikers/9999/rol", data={"rol": "kijker"}, follow_redirects=True)
    assert "bestaat niet" in r.text


def test_het_scherm_gebruikers_toont_de_rol_en_alleen_de_acties_van_de_beheerder(scherm, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    tekst = scherm.get("/gebruikers").text
    rij_anna = tekst[tekst.index(">anna (jij)<"):tekst.index(">bert<")]
    assert "Beheerder</td>" in rij_anna and "Maak kijker" in rij_anna and "Blokkeren" not in rij_anna
    rij_bert = tekst[tekst.index(">bert<"):]
    assert "Kijker</td>" in rij_bert and "Maak beheerder" in rij_bert and "Blokkeren" in rij_bert


def test_het_log_toont_de_rolwijziging_in_het_technische_log_en_de_gebruiker_als_gebruiker(scherm, twee):
    anna, _, bert = twee
    beheerders.rol_wijzigen(bert.id, "kijker", actor(anna))
    assert "beheerder.rol_gewijzigd" in log.TECHNISCH
    tekst = scherm.get("/log/techniek").text
    assert "beheerder.rol_gewijzigd" in tekst and "rol: [&#39;beheerder&#39;, &#39;kijker&#39;]" in tekst
    assert "beheerder.rol_gewijzigd" not in scherm.get("/log").text
    assert logacties().count("beheerder.rol_gewijzigd") == 1


# Migratie 0022


def rol_kolom(cfg):
    """(is_nullable, column_default) van beheerder.rol, of None zonder kolom."""
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as c:
        rij = c.execute(text("SELECT is_nullable, column_default FROM information_schema.columns "
                             "WHERE table_name = 'beheerder' AND column_name = 'rol'")).first()
    engine.dispose()
    return tuple(rij) if rij else None


def api_leest_rol(cfg):
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as c:
        recht = c.execute(text("SELECT has_column_privilege('botenloods_api', 'beheerder', 'rol', 'SELECT')")).scalar()
    engine.dispose()
    return recht


def test_migratie_0022_maakt_bestaande_accounts_beheerder_zonder_standaardwaarde(database):
    """Upgrade: bestaande accounts worden beheerder, de standaardwaarde vervalt, api mag de kolom lezen."""
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0021")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.begin() as c:
        c.execute(text("INSERT INTO beheerder (naam, gebruikersnaam) VALUES ('Oud', 'oud')"))
    assert rol_kolom(cfg) is None
    command.upgrade(cfg, "0022")
    with engine.connect() as c:
        assert c.execute(text("SELECT rol FROM beheerder")).scalars().all() == ["beheerder"]
        with pytest.raises(IntegrityError):
            c.execute(text("INSERT INTO beheerder (naam, gebruikersnaam) VALUES ('Nieuw', 'nieuw')"))
    engine.dispose()
    assert rol_kolom(cfg) == ("NO", None) and api_leest_rol(cfg) is True


def test_migratie_0022_check_rol_geldig(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0022")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as c, pytest.raises(IntegrityError, match="rol_geldig"):
        c.execute(text("INSERT INTO beheerder (naam, gebruikersnaam, rol) VALUES ('X', 'x', 'admin')"))
    engine.dispose()


def test_migratie_0022_api_leest_de_rol_maar_niet_de_gebruikersnaam(app, twee):
    """Het recht uit de migratie: SELECT (rol) voor botenloods_api, tokencontrole (ADR-015). Zonder dit recht
    faalt elke aanroep met een persoonlijk token; zie test_een_token_van_een_beheerder_werkt_nog."""
    engine = create_engine(API)
    with engine.connect() as c:
        assert sorted(c.execute(text("SELECT rol FROM beheerder")).scalars()) == ["beheerder", "beheerder"]
        with pytest.raises(ProgrammingError, match="permission denied"):
            c.execute(text("SELECT gebruikersnaam FROM beheerder"))
        c.rollback()
        with pytest.raises(ProgrammingError, match="permission denied"):
            c.execute(text("UPDATE beheerder SET rol = 'kijker'"))
    engine.dispose()


def test_migratie_0022_web_schrijft_de_rol_met_de_tabelrechten_van_0001(app, twee):
    """Er is geen nieuw recht voor web nodig: UPDATE op de tabel dekt de kolom (rol_wijzigen draait als web)."""
    assert db.session.execute(text("SELECT current_user")).scalar() == "botenloods_web"
    beheerders.rol_wijzigen(twee[2].id, "kijker", actor(twee[0]))
    assert rol_van(twee[2]) == "kijker"


def test_migratie_0022_downgrade_blokkeert_elke_kijker_en_upgrade_laat_ze_geblokkeerd(database):
    cfg = nieuwe_database("botenloods_migratie")
    command.upgrade(cfg, "0022")
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.begin() as c:
        c.execute(text("INSERT INTO beheerder (naam, gebruikersnaam, rol) VALUES ('Anna', 'anna', 'beheerder'), "
                       "('Kees', 'kees', 'kijker'), ('Lies', 'lies', 'kijker')"))
        c.execute(text("UPDATE beheerder SET actief = false WHERE gebruikersnaam = 'lies'"))
    command.downgrade(cfg, "0021")
    with engine.connect() as c:
        assert rol_kolom(cfg) is None
        rijen = c.execute(text("SELECT gebruikersnaam, actief, sessieversie FROM beheerder ORDER BY id")).all()
        assert [tuple(r) for r in rijen] == [("anna", True, 1), ("kees", False, 2), ("lies", False, 2)]
        regels = c.execute(text("SELECT actor_soort, actor_id, actor_naam, actie, verwijzingen, gegevens "
                                "FROM logregel ORDER BY id")).all()
    # Alleen de kijker die nog actief was krijgt een regel: de geblokkeerde was al geblokkeerd.
    assert [tuple(r) for r in regels] == [("systeem", None, "migratie", "beheerder.geblokkeerd",
                                           ["beheerder:2"], {"gebruikersnaam": "kees"})]
    command.upgrade(cfg, "0022")
    with engine.connect() as c:
        assert [tuple(r) for r in c.execute(text("SELECT gebruikersnaam, rol, actief FROM beheerder ORDER BY id"))] == [
            ("anna", "beheerder", True), ("kees", "beheerder", False), ("lies", "beheerder", False)]
    engine.dispose()


def test_een_token_van_een_verdwenen_eigenaar_geeft_eigenaar_inactief(app, twee):
    """AEG-02: een persoonlijk token zonder eigenaar (None) is eigenaar_inactief, geen fout 500."""
    from unittest import mock

    from app.domein import tokens
    waarde = persoonlijk(twee[2], "bert-laptop")
    with mock.patch.object(db.session, "execute") as uitvoeren:
        uitvoeren.return_value.one_or_none.return_value = None
        with pytest.raises(tokens.Geweigerd) as fout:
            tokens.controleer(f"Bearer {waarde}", "10.203.0.5", None, "x")
    assert fout.value.reden == "eigenaar_inactief" and fout.value.status == 401
