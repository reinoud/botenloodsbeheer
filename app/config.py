"""Instellingen uit de omgeving (ADR-009). Eén keer gelezen bij het starten."""

import ipaddress
import os
from datetime import datetime, timedelta
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


DIENSTEN = ("web", "worker", "api")
UPLOAD_MAX = 10 * 1024 * 1024  # gelijk aan de buffering van de router /boten (ADR-008)
IMPORT_MAX = 2 * 1024 * 1024  # PUT /api/v1/leden; Traefik heeft 3 MB als buitengrens


def _schakelaar(naam, standaard):
    waarde = _lees(naam, standaard)
    if waarde not in ("true", "false"):
        raise ConfigFout(f"{naam} moet true of false zijn")
    return waarde == "true"


def _tijdstip(naam, standaard):
    waarde = _lees(naam, standaard)
    try:
        return datetime.strptime(waarde, "%H:%M").time()
    except ValueError:
        raise ConfigFout(f"{naam} moet een tijdstip zijn zoals 04:00") from None


def laad():
    omgeving = _lees("APP_OMGEVING", "productie")
    # De worker en de api krijgen geen sessie- en TOTP-sleutel mee (#7): ze gebruiken ze niet.
    dienst = _lees("DIENST", "web")
    if dienst not in DIENSTEN:
        raise ConfigFout(f"DIENST moet een van {', '.join(DIENSTEN)} zijn")
    basis_url = _verplicht("BASIS_URL").rstrip("/")
    if omgeving == "productie" and not basis_url.startswith("https://"):
        raise ConfigFout("BASIS_URL moet in productie met https:// beginnen")
    # De routers van Traefik gebruiken DOMEIN; de applicatie BASIS_URL (ADR-013).
    if _verplicht("DOMEIN") != urlsplit(basis_url).hostname:
        raise ConfigFout("DOMEIN moet gelijk zijn aan de host uit BASIS_URL")
    # Alleen web draagt de routers met TLS; zonder certresolver toont Traefik zijn eigen certificaat.
    if dienst == "web" and omgeving == "productie" and not _lees("TRAEFIK_CERTRESOLVER"):
        raise ConfigFout("TRAEFIK_CERTRESOLVER ontbreekt in de omgeving (verplicht in productie)")

    koppelnet = _lees("KOPPELNET", "10.203.0.0/24")
    try:
        ipaddress.ip_network(koppelnet)
    except ValueError:
        raise ConfigFout("KOPPELNET moet een reeks zijn zoals 10.203.0.0/24") from None

    totp_sleutel = secret_key = None
    if dienst == "web":
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
        "DIENST": dienst,
        "API_INGESCHAKELD": _schakelaar("API_INGESCHAKELD", "true"),
        "KOPPELNET": koppelnet,
        "SECRET_KEY": secret_key,
        "SQLALCHEMY_DATABASE_URI": _verplicht("DATABASE_URL"),
        # Geen parameters in een SQL-fout: die komt met traceback in de log (#137) en bevat
        # anders persoonsgegevens. De DETAIL van PostgreSQL haalt _JsonLog weg.
        "SQLALCHEMY_ENGINE_OPTIONS": {"hide_parameters": True},
        "BASIS_URL": basis_url,
        "TOTP_SLEUTEL": totp_sleutel,
        "WEBAUTHN_RP_ID": _lees("WEBAUTHN_RP_ID") or urlsplit(basis_url).hostname,
        "PROXY_HOPS": int(_lees("PROXY_HOPS", "1")),
        "TZ": _lees("TZ", "Europe/Amsterdam"),
        # De dagelijkse opschoning in de worker, in de tijdzone TZ (ADR-007).
        "OPSCHOON_TIJDSTIP": _tijdstip("OPSCHOON_TIJDSTIP", "04:00"),
        # Buildargument van het image (ADR-010), voor de statuspagina.
        "APP_VERSIE": _lees("APP_VERSIE", "onbekend"),
        "LOG_NIVEAU": _lees("LOG_NIVEAU", "INFO"),
        # Alleen de dev-stack zet dit aan: Gunicorn --reload herlaadt geen templates (#114).
        "TEMPLATES_AUTO_RELOAD": _schakelaar("TEMPLATES_AUTO_RELOAD", "false"),
        # Alleen web toont het logo; de worker leest het niet (ADR-008).
        "LOGO_BESTAND": _lees("LOGO_BESTAND", "/huisstijl/logo.png") if dienst == "web" else None,
        "MAX_CONTENT_LENGTH": IMPORT_MAX if dienst == "api" else UPLOAD_MAX,
        "SESSION_COOKIE_SECURE": basis_url.startswith("https://"),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=12),
    }
