"""Foto's en logo (ADR-008): controleren, verkleinen en zonder metadata opslaan. Alleen foto's
komen in de database; het logo uit de installatie houdt web in het geheugen."""

import io
import secrets

from PIL import Image, ImageOps
from sqlalchemy import select

from app.domein import Regelfout
from app.models import Afbeelding, db

TOEGESTAAN = {"JPEG", "PNG", "WEBP"}  # op inhoud, niet op bestandsnaam; geen SVG
MAX_PIXELS = 40_000_000  # grens tegen decompressiebommen, ruim boven een telefoonfoto
LANGE_ZIJDE = {"foto": 1600, "logo": 800}
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

# shortcut: afbeeldingen in PostgreSQL (bytea); boven ongeveer 1000 foto's overstappen naar een
# volume, een beperkte wijziging in deze module en de route /afbeelding (ADR-008).


def verwerk(inhoud, soort="foto"):
    """Geeft een nieuwe, nog niet opgeslagen Afbeelding, of een Regelfout."""
    try:
        with Image.open(io.BytesIO(inhoud), formats=sorted(TOEGESTAAN)) as img:
            if img.format not in TOEGESTAAN or img.width * img.height > MAX_PIXELS:
                raise Regelfout(f"Kies een {soort} in JPEG, PNG of WebP.")
            img = ImageOps.exif_transpose(img)
            img.thumbnail((LANGE_ZIJDE[soort],) * 2)
            uit = io.BytesIO()
            # Opnieuw opslaan zonder exif of andere metadata (GPS-locatie).
            if soort == "foto":
                img.convert("RGB").save(uit, "JPEG", quality=85)
                mime = "image/jpeg"
            else:
                # PNG kent geen CMYK of YCbCr; met alfakanaal blijft transparantie staan.
                if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                    img = img.convert("RGBA")
                img.save(uit, "PNG", icc_profile=None)  # ook geen kleurprofiel van de bron
                mime = "image/png"
    except Regelfout:
        raise
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        raise Regelfout("Dit bestand is geen geldige afbeelding in JPEG, PNG of WebP. "
                        "De vorige blijft staan.") from None
    return Afbeelding(soort=soort, mime_type=mime, inhoud=uit.getvalue(), breedte=img.width,
                      hoogte=img.height, sleutel=secrets.token_urlsafe(12))


def op_sleutel(sleutel):
    return db.session.scalar(select(Afbeelding).where(Afbeelding.sleutel == sleutel))
