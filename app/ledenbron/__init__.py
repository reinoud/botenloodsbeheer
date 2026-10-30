"""Ledenbron (ADR-004): de enige module die met een extern systeem praat.

Een bron levert ruwe records; validatie en opslag zitten in domein/leden, zodat elke bron
dezelfde regels krijgt. Een nieuwe bron is een klasse hier en een waarde voor LEDENBRON.
"""

import json

from flask import current_app


class LedenbronFout(Exception):
    """Storing of onleesbaar antwoord. De tekst komt in taakrun en log: zonder geheimen."""


class NietBeschikbaar(Exception):
    pass


class Ledenbron:
    kan_terugschrijven = False

    def haal_leden(self):
        """Lijst van dicts met lidnummer, naam, adres, telefoon, email, lid_sinds en
        opzegdatum (datums als JJJJ-MM-DD). Gooit LedenbronFout."""
        raise NotImplementedError

    def schrijf_bootaantallen(self, aantallen):
        raise NietBeschikbaar("Terugschrijven is in deze versie niet beschikbaar.")


class StubBron(Ledenbron):
    """Leest leden uit een JSON-bestand. Ook de nepbron in de tests."""

    def __init__(self, pad):
        self.pad = pad

    def haal_leden(self):
        try:
            with open(self.pad, encoding="utf-8") as f:
                records = json.load(f)
        except OSError:
            raise LedenbronFout("De ledenbron is niet bereikbaar.") from None
        except ValueError:
            raise LedenbronFout("Het antwoord van de ledenbron is onleesbaar.") from None
        if not isinstance(records, list):
            raise LedenbronFout("Het antwoord van de ledenbron is onleesbaar.")
        return records


def kies():
    """De bron uit LEDENBRON. Zonder bron wijzigt de synchronisatie niets (BLB-007)."""
    naam = current_app.config["LEDENBRON"]
    if naam == "stub":
        return StubBron(current_app.config["LEDENBRON_STUB_BESTAND"])
    raise LedenbronFout("Er is geen ledenbron ingesteld.")
