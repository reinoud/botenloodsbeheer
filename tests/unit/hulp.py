"""Hulpfuncties voor tests: beheerders, leden en afbeeldingen aanmaken."""

import io
import time

import pyotp
from PIL import Image

from app.domein import CLI, beheerders
from app.models import Lid, db

WACHTWOORD = "correct paard batterij"


def code_bij(geheim, stappen_verder=0):
    return pyotp.TOTP(geheim).at(time.time() + 30 * stappen_verder)


def beheerder_met_wachtwoord(gebruikersnaam="anna"):
    """Geeft (beheerder, totp-geheim). De huidige tijdstap is al gebruikt."""
    code = beheerders.uitnodigen(gebruikersnaam, CLI)
    geheim = beheerders.nieuw_totp_geheim()
    b = beheerders.wachtwoord_instellen(code, WACHTWOORD, geheim, code_bij(geheim))
    return b, geheim


def png(breedte=40, hoogte=30, exif=None, formaat="PNG"):
    """Een kleine afbeelding als bytes, eventueel met exif (zoals GPS van een telefoon)."""
    uit = io.BytesIO()
    img = Image.new("RGB", (breedte, hoogte), (200, 80, 40))
    img.save(uit, formaat, **({"exif": exif} if exif else {}))
    return uit.getvalue()


def lid(lidnummer="1001", naam="Anna de Vries", **velden):
    """Een lid zoals de synchronisatie het aanmaakt; in tests direct in de database."""
    nieuw = Lid(lidnummer=lidnummer, naam=naam, adres="Proefweg 1, 1234 AB Voorbeelddorp",
                telefoon="06-00001234", email=f"{lidnummer}@example.org", **velden)
    db.session.add(nieuw)
    db.session.commit()
    return nieuw
