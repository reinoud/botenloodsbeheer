"""Hulpfuncties voor tests: beheerders, leden en afbeeldingen aanmaken."""

import io
import os
import threading
import time
from unittest import mock

import pyotp
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.domein import CLI, Regelfout, beheerders
from app.models import Lid, db
from tests.unit.conftest import API, WEB

WACHTWOORD = "correct paard batterij"


def code_bij(geheim, stappen_verder=0):
    return pyotp.TOTP(geheim).at(time.time() + 30 * stappen_verder)


def beheerder_met_wachtwoord(gebruikersnaam="anna"):
    """Geeft (beheerder, totp-geheim). De huidige tijdstap is al gebruikt."""
    code = beheerders.uitnodigen(gebruikersnaam, CLI)
    geheim = beheerders.nieuw_totp_geheim()
    b = beheerders.wachtwoord_instellen(code, WACHTWOORD, geheim, code_bij(geheim))
    return b, geheim


def png(breedte=40, hoogte=30, exif=None, formaat="PNG", icc=None):
    """Een kleine afbeelding als bytes, eventueel met exif (zoals GPS van een telefoon) of kleurprofiel."""
    uit = io.BytesIO()
    img = Image.new("RGB", (breedte, hoogte), (200, 80, 40))
    img.save(uit, formaat, **({"exif": exif} if exif else {}), **({"icc_profile": icc} if icc else {}))
    return uit.getvalue()


def _als(dienst, rol, functie, *args):
    from app import create_app

    with mock.patch.dict(os.environ, DIENST=dienst):
        andere = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": rol})
    with andere.app_context():
        resultaat = functie(*args)
        db.session.remove()
        db.engine.dispose()
    return resultaat


def als_web(functie, *args):
    """Draait functie in een app van de dienst web, zoals de CLI of de webinterface; voor tests
    die als een andere dienst draaien."""
    return _als("web", WEB, functie, *args)


def als_api(functie, *args):
    """Draait functie als de dienst api, zoals een import via PUT /api/v1/leden."""
    return _als("api", API, functie, *args)


def lid(lidnummer="1001", naam="Anna de Vries", **velden):
    """Een lid zoals de import het aanmaakt, als de rol van de dienst api: de webrol mag leden
    alleen lezen. Geeft het lid in de sessie van de test."""
    engine = create_engine(API)
    with Session(engine) as taak:
        nieuw = Lid(lidnummer=lidnummer, naam=naam, adres="Proefweg 1, 1234 AB Voorbeelddorp",
                    telefoon="06-00001234", email=f"{lidnummer}@example.org", **velden)
        taak.add(nieuw)
        taak.commit()
        lid_id = nieuw.id
    engine.dispose()
    return db.session.get(Lid, lid_id)


def race(app, sql, params, actie):
    """Twee databasesessies. De eerste vergrendelt een rij en wijzigt die met de SQL-regels in
    sql (de eerste regel is de SELECT ... FOR UPDATE). Intussen draait actie in een tweede sessie
    en moet wachten tot de eerste commit. Geeft de meldingen van de Regelfouten van actie."""
    fouten = []

    def tweede():
        with app.app_context():
            try:
                actie()
            except Regelfout as fout:
                fouten.append(str(fout))

    engine = create_engine(WEB)
    with engine.connect() as eerste:
        for regel in sql:
            eerste.execute(text(regel), params)
            if regel is sql[0]:
                draad = threading.Thread(target=tweede)
                draad.start()
                draad.join(timeout=1)
                assert draad.is_alive(), "de tweede sessie wacht niet op de vergrendeling"
        eerste.commit()
    draad.join(timeout=5)
    engine.dispose()
    db.session.expire_all()
    return fouten
