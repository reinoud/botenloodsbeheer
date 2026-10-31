"""Domeinlaag: de enige laag die gegevens wijzigt (architectuur §3)."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app


class Regelfout(Exception):
    """Een geweigerde wijziging met een vaste reden die de gebruiker mag zien."""


@dataclass(frozen=True)
class Actor:
    soort: str  # beheerder, token, taak of systeem
    id: int | None
    naam: str

    @classmethod
    def van(cls, beheerder):
        return cls("beheerder", beheerder.id, beheerder.gebruikersnaam)


CLI = Actor("systeem", None, "cli")
SYSTEEM = Actor("systeem", None, "systeem")


def vandaag():
    """De datum in de tijdzone van de installatie (TZ)."""
    return datetime.now(ZoneInfo(current_app.config["TZ"])).date()
