"""Instellingen uit de omgeving (ADR-009). Eén keer gelezen bij het starten."""

import os
from datetime import timedelta
from urllib.parse import urlsplit

from cryptography.fernet import Fernet


class ConfigFout(RuntimeError):
    pass


def _lees(naam, standaard=None):
    """Leest NAAM, of het bestand uit NAAM_FILE (Docker secret)."""
    pad = os.environ.get(f"{naam}_FILE")
    if pad:
        with open(pad) as f:
            return f.read().strip()
    return os.environ.get(naam, standaard)


def _verplicht(naam):
    waarde = _lees(naam)
    if not waarde:
        raise ConfigFout(f"{naam} ontbreekt in de omgeving")
    return waarde


def laad():
    omgeving = _lees("APP_OMGEVING", "productie")
    basis_url = _verplicht("BASIS_URL").rstrip("/")
    if omgeving == "productie" and not basis_url.startswith("https://"):
        raise ConfigFout("BASIS_URL moet in productie met https:// beginnen")

    totp_sleutel = _verplicht("TOTP_SLEUTEL")
    try:
        Fernet(totp_sleutel)
    except ValueError:
        raise ConfigFout("TOTP_SLEUTEL is geen geldige Fernet-sleutel") from None

    secret_key = _verplicht("SECRET_KEY")
    if len(secret_key) < 32:
        raise ConfigFout("SECRET_KEY moet minstens 32 tekens lang zijn")

    return {
        "APP_OMGEVING": omgeving,
        "SECRET_KEY": secret_key,
        "SQLALCHEMY_DATABASE_URI": _verplicht("DATABASE_URL"),
        "BASIS_URL": basis_url,
        "TOTP_SLEUTEL": totp_sleutel,
        "WEBAUTHN_RP_ID": _lees("WEBAUTHN_RP_ID") or urlsplit(basis_url).hostname,
        "PROXY_HOPS": int(_lees("PROXY_HOPS", "1")),
        "TZ": _lees("TZ", "Europe/Amsterdam"),
        "LOG_NIVEAU": _lees("LOG_NIVEAU", "INFO"),
        "SESSION_COOKIE_SECURE": basis_url.startswith("https://"),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=12),
    }
