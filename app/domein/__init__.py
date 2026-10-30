"""Domeinlaag: de enige laag die gegevens wijzigt (architectuur §3)."""

from dataclasses import dataclass


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
