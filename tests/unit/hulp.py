"""Hulpfuncties voor tests: beheerders, leden, plaatsen en afbeeldingen aanmaken."""

import io
import os
import threading
import time
from unittest import mock

import pyotp
from PIL import Image
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.domein import CLI, Regelfout, beheerders, indeling
from app.models import Lid, Rek, db
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


def png(breedte=40, hoogte=30, exif=None, formaat="PNG", icc=None, **extra):
    """Een kleine afbeelding als bytes, eventueel met exif (GPS van een telefoon), kleurprofiel
    of andere opties van Pillow (zoals comment)."""
    uit = io.BytesIO()
    img = Image.new("RGB", (breedte, hoogte), (200, 80, 40))
    if exif:
        extra["exif"] = exif
    if icc:
        extra["icc_profile"] = icc
    img.save(uit, formaat, **extra)
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
        nieuw = Lid(lidnummer=lidnummer, naam=naam, **velden)
        taak.add(nieuw)
        taak.commit()
        lid_id = nieuw.id
    engine.dispose()
    return db.session.get(Lid, lid_id)


def plaats(code="A/1/1", soort_ids=(1,), club=False):
    """De plaats met aanduiding code (<rek>/<verdieping>/<vak>), in het rek met die naam; het rek
    komt erbij als het er nog niet is (ADR-003). soort_ids zijn de geschikte bootsoorten."""
    naam, verdieping, vak = code.rsplit("/", 2)
    vak_aan = (int(verdieping), int(vak))
    r = db.session.scalar(select(Rek).where(func.lower(Rek.naam) == naam.lower()))
    if r is None:
        r = indeling.rek_aanmaken(naam, "", {vak_aan}, CLI)
    else:
        indeling.indeling_instellen(r.id, {(p.verdieping, p.vak) for p in r.plaatsen} | {vak_aan},
                                    CLI)
    p = next(p for p in r.plaatsen if (p.verdieping, p.vak) == vak_aan)
    return indeling.plaats_wijzigen(p.id, list(soort_ids), club, CLI)


def logo_zetten(inhoud=None):
    """Zoals de beheerder op Instellingen; geeft het kenmerk van het logo."""
    from app.domein import instellingen
    instellingen.logo_vervangen(inhoud or png(), CLI)
    return instellingen.logo()


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
