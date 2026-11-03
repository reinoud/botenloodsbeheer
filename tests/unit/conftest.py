"""Tests tegen een echte PostgreSQL in compose (architectuur §6.5).

De eigenaar maakt een lege database botenloods_test en draait de migraties. De applicatie
verbindt als botenloods_web, net als in productie; met de markering worker als botenloods_taken
en met api als de dienst api (botenloods_api). Na elke test worden de tabellen geleegd.
"""

import os

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text

TEST_DB = "botenloods_test"
TABELLEN = ("beheerder, passkey, uitnodiging, logregel, instelling, taakrun, rek, plaats, "
            "plaats_bootsoort, lid, boot, wachtlijst, afbeelding, token, bootsoort")
# Na elke test weer de startlijst uit de migratie, ook als een test soorten wijzigde (BLB-028).
STARTLIJST = "INSERT INTO bootsoort (naam) VALUES " + ", ".join(
    f"('{naam}')" for naam in ("Kajak", "Canadese kano", "Surfski", "C11", "Supboard"))


def db_url(gebruiker, wachtwoord, database=TEST_DB):
    return f"postgresql+psycopg://{gebruiker}:{wachtwoord}@db/{database}"


EIGENAAR = db_url("botenloods", os.environ["POSTGRES_PASSWORD"])
WEB = db_url("botenloods_web", os.environ["DB_WEB_WACHTWOORD"])
TAKEN = db_url("botenloods_taken", os.environ["DB_TAKEN_WACHTWOORD"])
API = db_url("botenloods_api", os.environ["DB_API_WACHTWOORD"])

os.environ.update(
    APP_OMGEVING="test",
    SECRET_KEY="test-" + "x" * 40,
    TOTP_SLEUTEL=Fernet.generate_key().decode(),
    BASIS_URL="http://localhost:8080",
    DOMEIN="localhost",
    DATABASE_URL=WEB,
    LEDENBRON="stub",
    LEDENBRON_STUB_BESTAND="tests/fixtures/leden.json",
)


def nieuwe_database(naam):
    beheer = create_engine(db_url("botenloods", os.environ["POSTGRES_PASSWORD"], "postgres"),
                           isolation_level="AUTOCOMMIT")
    with beheer.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {naam} WITH (FORCE)"))
        c.execute(text(f"CREATE DATABASE {naam}"))
    beheer.dispose()
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url("botenloods", os.environ["POSTGRES_PASSWORD"], naam))
    return cfg


@pytest.fixture(scope="session")
def database():
    command.upgrade(nieuwe_database(TEST_DB), "head")
    eigenaar = create_engine(EIGENAAR)
    yield eigenaar
    eigenaar.dispose()


def pytest_configure(config):
    config.addinivalue_line("markers", "worker: de test draait als botenloods_taken, zoals de worker")
    config.addinivalue_line("markers", "api: de test draait als de dienst api (botenloods_api)")


@pytest.fixture
def app(database, request):
    from app import create_app
    from app.models import db

    rol = TAKEN if request.node.get_closest_marker("worker") else WEB
    api = request.node.get_closest_marker("api") is not None
    if api:
        rol = API
        request.getfixturevalue("monkeypatch").setenv("DIENST", "api")
    # De API draait met CSRF aan, zoals in productie: een PUT zonder vrijstelling faalt dan.
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": api, "SQLALCHEMY_DATABASE_URI": rol})
    with app.app_context():
        yield app
        db.session.remove()
        db.engine.dispose()
    with database.begin() as c:
        c.execute(text(f"TRUNCATE {TABELLEN} RESTART IDENTITY CASCADE"))
        c.execute(text(STARTLIJST))


@pytest.fixture
def client(app):
    return app.test_client()
