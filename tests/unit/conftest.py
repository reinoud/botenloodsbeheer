"""Tests tegen een echte PostgreSQL in compose (architectuur §6.5).

De eigenaar maakt een lege database botenloods_test en draait de migraties. De applicatie
verbindt als botenloods_web, net als in productie. Na elke test worden de tabellen geleegd.
"""

import os

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text

TEST_DB = "botenloods_test"
# bootsoort niet: de startlijst komt uit de migratie.
TABELLEN = ("beheerder, passkey, uitnodiging, logregel, instelling, taakrun, rek, plaats, "
            "plaats_bootsoort, lid, boot, afbeelding")


def db_url(gebruiker, wachtwoord, database=TEST_DB):
    return f"postgresql+psycopg://{gebruiker}:{wachtwoord}@db/{database}"


EIGENAAR = db_url("botenloods", os.environ["POSTGRES_PASSWORD"])
WEB = db_url("botenloods_web", os.environ["DB_WEB_WACHTWOORD"])
TAKEN = db_url("botenloods_taken", os.environ["DB_TAKEN_WACHTWOORD"])

os.environ.update(
    APP_OMGEVING="test",
    SECRET_KEY="test-" + "x" * 40,
    TOTP_SLEUTEL=Fernet.generate_key().decode(),
    BASIS_URL="http://localhost:8080",
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


@pytest.fixture
def app(database, request):
    from app import create_app
    from app.models import db

    rol = TAKEN if request.node.get_closest_marker("worker") else WEB
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": rol})
    with app.app_context():
        yield app
        db.session.remove()
        db.engine.dispose()
    with database.begin() as c:
        c.execute(text(f"TRUNCATE {TABELLEN} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(app):
    return app.test_client()
